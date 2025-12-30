from django.conf import settings
from django.db import models
from django.utils import timezone


class Room(models.Model):
    """Represents a single hotel room that can be booked.

    Pricing is split into hourly and daily base prices so the booking
    service can calculate total cost based on booking type.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=1)
    logo = models.TextField(
        blank=True,
        help_text="Base64 encoded image for room / hotel logo"
    )

    # Base prices; actual price is computed at booking time
    base_price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    base_price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(
        default=True,
        help_text="Inactive rooms are hidden from search and cannot be booked.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["base_price_per_hour"]),
            models.Index(fields=["base_price_per_day"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name


class Booking(models.Model):
    class Meta:
        ordering = ["-start_datetime"] 
    """Represents a single booking of a room for a given time range.

    All bookings use timezone-aware datetimes and UTC at the database level.
    Overlap checks and state transitions are implemented in the service layer,
    but core invariants live here as well for extra safety.
    """

    class BookingType(models.TextChoices):
        HOURLY = "HOURLY", "Hourly"
        DAILY = "DAILY", "Daily"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CHECKED_IN = "CHECKED_IN", "Checked in"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    booking_type = models.CharField(
        max_length=10,
        choices=BookingType.choices,
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    # Cached total price at the time of booking; allows future price
    # changes on the room without affecting existing bookings.
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_datetime"]
        indexes = [
            # Helps overlap checks and history queries
            models.Index(fields=["room", "start_datetime", "end_datetime", "status"]),
            models.Index(fields=["user", "start_datetime"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"Booking #{self.pk} - {self.room.name} ({self.booking_type})"

    # ---- Validation helpers -------------------------------------------------

    def clean(self):
        """Model-level validation for core invariants.

        Detailed business rules (such as overlap checks) are enforced in
        the service layer, but we still guard against obviously invalid
        data here.
        """

        from django.core.exceptions import ValidationError

        if self.start_datetime >= self.end_datetime:
            raise ValidationError("start_datetime must be before end_datetime.")

        # Prevent creating bookings that end in the past; this is a business
        # choice and can be relaxed if backfilling is needed in future.
        now = timezone.now()
        if self.end_datetime <= now:
            raise ValidationError("Booking end time must be in the future.")

        # Type-specific minimal durations
        duration = self.end_datetime - self.start_datetime
        if self.booking_type == self.BookingType.HOURLY and duration.total_seconds() < 3600:
            raise ValidationError("Hourly bookings must be at least 1 hour long.")
        if self.booking_type == self.BookingType.DAILY and duration.total_seconds() < 86400:
            raise ValidationError("Daily bookings must be at least 1 day long.")
        
    class Meta:
        ordering = ["-created_at", "-start_datetime"] 
        indexes = [
            models.Index(fields=["room", "start_datetime", "end_datetime", "status"]),
            models.Index(fields=["user", "start_datetime"]),
        ]

    # Lightweight helpers for status checks; main transitions live in services
    @property
    def is_active(self) -> bool:
        """Active bookings are those that still hold the room."""

        return self.status in {
            self.Status.PENDING,
            self.Status.CONFIRMED,
            self.Status.CHECKED_IN,
        }
