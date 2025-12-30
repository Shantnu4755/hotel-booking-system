from django.contrib import admin
from .models import Room, Booking


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'base_price_per_hour', 'base_price_per_day', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'room', 'booking_type', 'start_datetime', 'end_datetime', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'booking_type', 'created_at']
    search_fields = ['user__username', 'room__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_datetime'
