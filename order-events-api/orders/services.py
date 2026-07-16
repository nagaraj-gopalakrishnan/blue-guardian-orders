"""
Webhook ingestion logic.

Conflict-resolution rule (explicit):
    The event with the LATEST `event_timestamp` determines the order's
    current status, regardless of the order in which events arrived.
    If two events carry the exact same `event_timestamp` (from different
    sources), the one that was received first wins — a deterministic,
    documented tie-break.

Idempotency rule:
    (order_id, event_timestamp, source) uniquely identifies an event.
    Redeliveries of the same triple are acknowledged but not re-processed.
"""
from dataclasses import dataclass

from django.db import transaction

from .models import Order, OrderEvent


@dataclass
class IngestResult:
    order: Order
    event: OrderEvent
    duplicate: bool


def recompute_order_state(order: Order) -> None:
    """
    Re-derive the order's current state from its full event history.

    `event_timestamp` is the source of truth — never insertion order.
    `id` (monotonic insert order) only breaks exact-timestamp ties:
    among events with the same latest timestamp, the first one received
    wins.
    """
    winner = order.events.order_by("-event_timestamp", "id").first()
    if winner is None:  # pragma: no cover - an order always has >= 1 event
        return
    order.current_status = winner.status
    order.last_source = winner.source
    order.last_event_timestamp = winner.event_timestamp
    order.save(update_fields=["current_status", "last_source", "last_event_timestamp", "updated_at"])


@transaction.atomic
def ingest_event(*, order_id: str, status: str, event_timestamp, source: str) -> IngestResult:
    """
    Record a webhook event and reconcile the order's current state.

    Safe to call concurrently: the row lock on Order serializes ingestion
    per order, and the unique constraint on OrderEvent guarantees a
    duplicate delivery can never be stored (or processed) twice.
    """
    order, _ = Order.objects.select_for_update().get_or_create(
        order_id=order_id,
        defaults={
            "current_status": status,
            "last_source": source,
            "last_event_timestamp": event_timestamp,
        },
    )

    event, created = OrderEvent.objects.get_or_create(
        order=order,
        event_timestamp=event_timestamp,
        source=source,
        defaults={"status": status},
    )
    if not created:
        # Duplicate delivery: acknowledge, do not re-process.
        return IngestResult(order=order, event=event, duplicate=True)

    recompute_order_state(order)
    return IngestResult(order=order, event=event, duplicate=False)
