"""Domain services for the bookings app.

This module contains the core business logic for searching availability,
creating bookings, and handling lifecycle transitions. Keeping these
functions separate from views and serializers helps the codebase scale
cleanly as the project grows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_UP
from typing import Iterable, List

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Booking, Room


@dataclass
class AvailabilityRequest:
    """Strongly-typed input object for availability/search operations."""

    start: timezone.datetime
    end: timezone.datetime
    booking_type: str


def _ceil_division(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Ceil division that works with decimals.

    For example, 1.1 hours should be charged as 2 hours.
    """

    return (numerator / denominator).to_integral_value(rounding=ROUND_UP)


def calculate_price(*, room: Room, start, end, booking_type: str) -> Decimal:
    """Calculate total price based on booking type and duration.

    Hourly:  ceil(total_hours)  * base_price_per_hour
    Daily:   ceil(total_days)   * base_price_per_day
    """

    total_seconds = Decimal((end - start).total_seconds())

    if booking_type == Booking.BookingType.HOURLY:
        hours = _ceil_division(total_seconds, Decimal(3600))
        return hours * room.base_price_per_hour

    if booking_type == Booking.BookingType.DAILY:
        days = _ceil_division(total_seconds, Decimal(86400))
        return days * room.base_price_per_day

    raise ValueError(f"Unsupported booking_type: {booking_type}")


def get_overlapping_bookings(*, room: Room, start, end) -> Iterable[Booking]:
    """Return bookings that overlap the given time range for a room.

    Overlap condition for [A_start, A_end) and [B_start, B_end):

        A_start < B_end AND A_end > B_start

    Only active (non-canceled, non-completed) bookings are considered.
    """

    return Booking.objects.select_for_update().filter(
        room=room,
        status__in=[
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
            Booking.Status.CHECKED_IN,
        ],
    ).filter(
        start_datetime__lt=end,
        end_datetime__gt=start,
    )


def search_available_rooms(request: AvailabilityRequest) -> List[Room]:
    """Return rooms that are free for the requested time range.

    This function is read-only; it does not use select_for_update because
    it is used by search endpoints, not by booking creation itself.
    """

    # Start with all active rooms
    qs = Room.objects.filter(is_active=True)

    # Rooms that have a conflicting booking in the requested window
    conflicting_room_ids = (
        Booking.objects.filter(
            room__is_active=True,
            status__in=[
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
                Booking.Status.CHECKED_IN,
            ],
        )
        .filter(
            start_datetime__lt=request.end,
            end_datetime__gt=request.start,
        )
        .values_list("room_id", flat=True)
        .distinct()
    )

    return list(qs.exclude(id__in=conflicting_room_ids))


@transaction.atomic
def create_booking(*, user, room: Room, start, end, booking_type: str) -> Booking:
    """Create a booking with full validation, overlap check, and pricing.

    This function runs in a transaction and uses select_for_update() on
    potentially overlapping bookings to avoid race conditions and double
    bookings under high concurrency.
    """

    now = timezone.now()
    if end <= now:
        raise ValueError("Booking end time must be in the future.")

    # Lock existing overlapping bookings for this room to prevent races
    overlapping = list(get_overlapping_bookings(room=room, start=start, end=end))
    if overlapping:
        raise ValueError("This room is already booked for the selected time range.")

    total_price = calculate_price(room=room, start=start, end=end, booking_type=booking_type)

    booking = Booking(
        user=user,
        room=room,
        booking_type=booking_type,
        start_datetime=start,
        end_datetime=end,
        status=Booking.Status.CONFIRMED,
        total_price=total_price,
    )

    # Run model-level validation as a safety net
    booking.full_clean()
    booking.save()

    return booking


@transaction.atomic
def check_in(booking: Booking) -> Booking:
    """Transition a booking to CHECKED_IN if rules allow it."""

    now = timezone.now()

    if booking.status not in {Booking.Status.CONFIRMED, Booking.Status.PENDING}:
        raise ValueError("Only confirmed or pending bookings can be checked in.")

    if now < booking.start_datetime:
        raise ValueError("Cannot check in before the booking start time.")

    if now >= booking.end_datetime:
        raise ValueError("Cannot check in after the booking has already ended.")

    booking.status = Booking.Status.CHECKED_IN
    booking.save(update_fields=["status", "updated_at"])
    return booking


@transaction.atomic
def check_out(booking: Booking) -> Booking:
    """Transition a booking to COMPLETED if rules allow it."""

    if booking.status != Booking.Status.CHECKED_IN:
        raise ValueError("Only checked-in bookings can be checked out.")

    booking.status = Booking.Status.COMPLETED
    booking.save(update_fields=["status", "updated_at"])
    return booking


@transaction.atomic
def cancel_booking(booking: Booking) -> Booking:
    """Cancel a booking if it has not started yet and is not already final."""

    now = timezone.now()

    if booking.status in {Booking.Status.COMPLETED, Booking.Status.CANCELED}:
        raise ValueError("Completed or canceled bookings cannot be modified.")

    if now >= booking.start_datetime:
        raise ValueError("Cannot cancel a booking on or after its start time.")

    booking.status = Booking.Status.CANCELED
    booking.save(update_fields=["status", "updated_at"])
    return booking


