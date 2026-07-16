from django.db import models


class Order(models.Model):
    """
    The current, reconciled view of an order.

    `current_status` / `last_source` / `last_event_timestamp` are a projection
    derived from the OrderEvent history using the rule:

        **the event with the latest `event_timestamp` wins**

    (ties on `event_timestamp` are broken by whichever event was received
    first — see orders.services.recompute_order_state).
    """

    order_id = models.CharField(max_length=100, unique=True)
    current_status = models.CharField(max_length=50)
    last_source = models.CharField(max_length=50)
    last_event_timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.order_id} [{self.current_status}]"


class OrderEvent(models.Model):
    """
    An immutable record of every webhook delivery we accepted.

    The unique constraint on (order, event_timestamp, source) is what makes
    the webhook idempotent: a redelivery of the same event hits the
    constraint and is skipped instead of being processed twice.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=50)
    source = models.CharField(max_length=50)
    event_timestamp = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "event_timestamp", "source"],
                name="uniq_order_event_timestamp_source",
            )
        ]
        indexes = [
            models.Index(
                fields=["order", "-event_timestamp"],
                name="idx_event_order_ts",
            )
        ]
        ordering = ["-event_timestamp", "id"]

    def __str__(self):
        return f"{self.order.order_id} {self.status} @ {self.event_timestamp} ({self.source})"
