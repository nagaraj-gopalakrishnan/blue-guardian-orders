from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import (
    OrderDetailSerializer,
    OrderSerializer,
    WebhookEventSerializer,
)
from .services import ingest_event


class OrderEventWebhookView(APIView):
    """
    POST /api/webhooks/order-events/

    Ingests a state-change event from an upstream system (payment
    processor, trading platform, ...). Idempotent: redelivering the same
    (order_id, event_timestamp, source) returns 200 without re-processing.
    """

    def post(self, request):
        serializer = WebhookEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = ingest_event(**serializer.validated_data)

        if result.duplicate:
            return Response(
                {
                    "detail": "Duplicate event ignored (already processed).",
                    "duplicate": True,
                    "order": OrderSerializer(result.order).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "detail": "Event processed.",
                "duplicate": False,
                "order": OrderSerializer(result.order).data,
            },
            status=status.HTTP_201_CREATED,
        )


class OrderListView(generics.ListAPIView):
    """GET /api/orders/ — all orders with their reconciled current state."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/<order_id>/ — one order plus its full event history."""

    queryset = Order.objects.prefetch_related("events")
    serializer_class = OrderDetailSerializer
    lookup_field = "order_id"
