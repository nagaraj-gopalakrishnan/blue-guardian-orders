from django.contrib import admin

from .models import Order, OrderEvent


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    readonly_fields = ["status", "source", "event_timestamp", "received_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_id", "current_status", "last_source", "last_event_timestamp", "updated_at"]
    search_fields = ["order_id"]
    inlines = [OrderEventInline]


@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    list_display = ["order", "status", "source", "event_timestamp", "received_at"]
    list_filter = ["source", "status"]
