from django.urls import path

from . import views

urlpatterns = [
    path("webhooks/order-events/", views.OrderEventWebhookView.as_view(), name="order-event-webhook"),
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path("orders/<str:order_id>/", views.OrderDetailView.as_view(), name="order-detail"),
]
