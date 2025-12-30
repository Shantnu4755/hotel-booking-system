"""High-level tests for the bookings app.

These tests cover overlapping booking prevention, price calculation,
and basic lifecycle transitions using Django's test framework and
DRF's APIClient.
"""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Booking, Room

User = get_user_model()


class BookingDomainTests(APITestCase):
    """Test core booking rules and lifecycle.

    We use API-level tests so that serializers, services, and views are
    exercised together, which is closer to how the system is used in
    practice.
    """

    def setUp(self):  # noqa: D401 - simple fixture setup
        """Create a user and a single room shared across tests."""

        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.force_authenticate(self.user)

        self.room = Room.objects.create(
            name="Deluxe Suite",
            description="Spacious suite with city view",
            capacity=2,
            base_price_per_hour=100,
            base_price_per_day=500,
        )

    def _create_booking(self, start, end, booking_type="HOURLY") -> Booking:
        url = reverse("bookings:booking-list")
        payload = {
            "room_id": self.room.id,
            "booking_type": booking_type,
            "start_datetime": start.isoformat().replace("+00:00", "Z"),
            "end_datetime": end.isoformat().replace("+00:00", "Z"),
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return Booking.objects.get(id=response.data["id"])

    def test_prevent_overlapping_bookings(self):
        """Second booking in the same time window for the same room must fail."""

        now = timezone.now()
        start = now + timedelta(hours=2)
        end = start + timedelta(hours=3)

        # First booking should succeed
        booking1 = self._create_booking(start, end, booking_type="HOURLY")
        self.assertEqual(booking1.status, Booking.Status.CONFIRMED)

        # Second booking with overlapping time should fail
        url = reverse("bookings:booking-list")
        payload = {
            "room_id": self.room.id,
            "booking_type": "HOURLY",
            "start_datetime": (start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
            "end_datetime": (end + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This room is already booked", str(response.data))

    def test_price_calculation_hourly_ceiling(self):
        """Hourly bookings should be rounded up to the next full hour for pricing."""

        now = timezone.now()
        start = now + timedelta(hours=1)
        # 1 hour 10 minutes should charge for 2 hours
        end = start + timedelta(hours=1, minutes=10)

        booking = self._create_booking(start, end, booking_type="HOURLY")
        # base_price_per_hour is 100, so 2 hours = 200
        self.assertEqual(float(booking.total_price), 200.0)

    def test_price_calculation_daily_ceiling(self):
        """Daily bookings should be rounded up to the next full day for pricing."""

        now = timezone.now()
        start = now + timedelta(days=1)
        # 1 day 1 hour should charge for 2 days
        end = start + timedelta(days=1, hours=1)

        booking = self._create_booking(start, end, booking_type="DAILY")
        # base_price_per_day is 500, so 2 days = 1000
        self.assertEqual(float(booking.total_price), 1000.0)

    def test_check_in_and_check_out_lifecycle(self):
        """Check-in then check-out should move booking through correct statuses."""

        now = timezone.now()
        start = now + timedelta(minutes=1)
        end = start + timedelta(hours=2)
        booking = self._create_booking(start, end, booking_type="HOURLY")

        # Move "now" forward just after start for the purpose of this test by
        # directly adjusting start_datetime.
        booking.start_datetime = timezone.now() - timedelta(minutes=1)
        booking.save(update_fields=["start_datetime"])

        check_in_url = reverse("bookings:booking-check-in", args=[booking.id])
        response = self.client.post(check_in_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CHECKED_IN)

        check_out_url = reverse("bookings:booking-check-out", args=[booking.id])
        response = self.client.post(check_out_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COMPLETED)

    def test_cannot_cancel_after_start_time(self):
        """Cancel should fail when current time is on or after start_datetime."""

        now = timezone.now()
        start = now + timedelta(minutes=1)
        end = start + timedelta(hours=1)
        booking = self._create_booking(start, end, booking_type="HOURLY")

        # Simulate a booking that already started
        booking.start_datetime = timezone.now() - timedelta(minutes=5)
        booking.save(update_fields=["start_datetime"])

        cancel_url = reverse("bookings:booking-cancel", args=[booking.id])
        response = self.client.post(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot cancel a booking", str(response.data))
