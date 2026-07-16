from rest_framework import serializers

from .models import Order, OrderEvent


class WebhookEventSerializer(serializers.Serializer):
    """Validates the inbound webhook payload."""

    order_id = serializers.CharField(max_length=100)
    status = serializers.CharField(max_length=50)
    event_timestamp = serializers.DateTimeField()
    source = serializers.CharField(max_length=50)


class OrderEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderEvent
        fields = ["id", "status", "source", "event_timestamp", "received_at"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "order_id",
            "current_status",
            "last_source",
            "last_event_timestamp",
            "created_at",
            "updated_at",
        ]


class OrderDetailSerializer(OrderSerializer):
    events = OrderEventSerializer(many=True, read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ["events"]
