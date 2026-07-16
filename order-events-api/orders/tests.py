"""
Tests for webhook idempotency, out-of-order handling, and conflict
resolution ("latest event_timestamp wins").
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Order, OrderEvent

WEBHOOK_URL = "/api/webhooks/order-events/"


def payload(order_id="ORD-1", status_="pending", ts="2026-07-16T10:00:00Z", source="payment_processor"):
    return {
        "order_id": order_id,
        "status": status_,
        "event_timestamp": ts,
        "source": source,
    }


class WebhookIngestionTests(APITestCase):
    def test_first_event_creates_order_and_event(self):
        resp = self.client.post(WEBHOOK_URL, payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resp.data["duplicate"])

        order = Order.objects.get(order_id="ORD-1")
        self.assertEqual(order.current_status, "pending")
        self.assertEqual(order.last_source, "payment_processor")
        self.assertEqual(order.events.count(), 1)

    def test_invalid_payload_rejected(self):
        resp = self.client.post(WEBHOOK_URL, {"order_id": "ORD-1"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_timestamp_rejected(self):
        resp = self.client.post(WEBHOOK_URL, payload(ts="not-a-date"), format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class IdempotencyTests(APITestCase):
    def test_duplicate_delivery_is_skipped(self):
        """Same (order_id, event_timestamp, source) must not double-process."""
        first = self.client.post(WEBHOOK_URL, payload(), format="json")
        dup = self.client.post(WEBHOOK_URL, payload(), format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(dup.status_code, status.HTTP_200_OK)
        self.assertTrue(dup.data["duplicate"])
        self.assertEqual(OrderEvent.objects.count(), 1)

    def test_duplicate_with_different_status_does_not_overwrite(self):
        """A redelivery is identified by the triple, not the status body."""
        self.client.post(WEBHOOK_URL, payload(status_="pending"), format="json")
        self.client.post(WEBHOOK_URL, payload(status_="paid"), format="json")

        order = Order.objects.get(order_id="ORD-1")
        self.assertEqual(order.current_status, "pending")
        self.assertEqual(OrderEvent.objects.count(), 1)

    def test_same_timestamp_different_source_is_not_a_duplicate(self):
        self.client.post(WEBHOOK_URL, payload(source="payment_processor"), format="json")
        resp = self.client.post(WEBHOOK_URL, payload(source="trading_platform"), format="json")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrderEvent.objects.count(), 2)


class OutOfOrderTests(APITestCase):
    def test_late_arriving_old_event_does_not_regress_status(self):
        """An older event arriving after a newer one must not win."""
        self.client.post(
            WEBHOOK_URL,
            payload(status_="executed", ts="2026-07-16T12:00:00Z", source="trading_platform"),
            format="json",
        )
        self.client.post(
            WEBHOOK_URL,
            payload(status_="pending", ts="2026-07-16T10:00:00Z", source="payment_processor"),
            format="json",
        )

        order = Order.objects.get(order_id="ORD-1")
        self.assertEqual(order.current_status, "executed")
        self.assertEqual(order.last_source, "trading_platform")
        self.assertEqual(order.events.count(), 2)  # history still keeps both

    def test_newer_event_updates_status(self):
        self.client.post(
            WEBHOOK_URL, payload(status_="pending", ts="2026-07-16T10:00:00Z"), format="json"
        )
        self.client.post(
            WEBHOOK_URL,
            payload(status_="filled", ts="2026-07-16T11:00:00Z", source="trading_platform"),
            format="json",
        )

        order = Order.objects.get(order_id="ORD-1")
        self.assertEqual(order.current_status, "filled")
        self.assertEqual(order.last_source, "trading_platform")


class ConflictResolutionTests(APITestCase):
    def test_latest_timestamp_wins_across_sources(self):
        """Payment processor and trading platform disagree: latest ts wins."""
        self.client.post(
            WEBHOOK_URL,
            payload(status_="paid", ts="2026-07-16T10:30:00Z", source="payment_processor"),
            format="json",
        )
        self.client.post(
            WEBHOOK_URL,
            payload(status_="cancelled", ts="2026-07-16T10:45:00Z", source="trading_platform"),
            format="json",
        )

        order = Order.objects.get(order_id="ORD-1")
        self.assertEqual(order.current_status, "cancelled")
        self.assertEqual(order.last_source, "trading_platform")

    def test_exact_timestamp_tie_first_received_wins(self):
        """Documented tie-break: same timestamp, first-received event wins."""
        self.client.post(
            WEBHOOK_URL,
            payload(status_="paid", ts="2026-07-16T10:30:00Z", source="payment_processor"),
            format="json",
        )
        self.client.post(
            WEBHOOK_URL,
            payload(status_="rejected", ts="2026-07-16T10:30:00Z", source="trading_platform"),
            format="json",
        )

        order = Order.objects.get(order_id="ORD-1")
        self.assertEqual(order.current_status, "paid")
        self.assertEqual(order.last_source, "payment_processor")


class ReadEndpointTests(APITestCase):
    def setUp(self):
        self.client.post(
            WEBHOOK_URL, payload(order_id="ORD-A", status_="pending", ts="2026-07-16T09:00:00Z"), format="json"
        )
        self.client.post(
            WEBHOOK_URL,
            payload(order_id="ORD-A", status_="filled", ts="2026-07-16T10:00:00Z", source="trading_platform"),
            format="json",
        )
        self.client.post(
            WEBHOOK_URL, payload(order_id="ORD-B", status_="paid", ts="2026-07-16T09:30:00Z"), format="json"
        )

    def test_list_orders_is_paginated(self):
        resp = self.client.get("/api/orders/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)
        by_id = {o["order_id"]: o for o in resp.data["results"]}
        self.assertEqual(by_id["ORD-A"]["current_status"], "filled")
        self.assertEqual(by_id["ORD-B"]["current_status"], "paid")

    def test_order_detail_includes_full_history(self):
        resp = self.client.get("/api/orders/ORD-A/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["current_status"], "filled")
        self.assertEqual(len(resp.data["events"]), 2)
        # History is ordered newest-first by event_timestamp.
        self.assertEqual(resp.data["events"][0]["status"], "filled")
        self.assertEqual(resp.data["events"][1]["status"], "pending")

    def test_order_detail_404(self):
        resp = self.client.get("/api/orders/NOPE/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
