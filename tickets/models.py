from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class ValidatedModel(models.Model):
    """Validate direct ORM writes as well as serializer writes."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        STANDARD = "standard", "Standard"

    role = models.CharField(max_length=8, choices=Role.choices, default=Role.STANDARD)

    class Meta(AbstractUser.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                condition=Q(role__in=["admin", "standard"]), name="valid_user_role"
            )
        ]


class Venue(ValidatedModel):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Seat(ValidatedModel):
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="seats")
    row = models.CharField(max_length=8)
    number = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["venue_id", "row", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["venue", "row", "number"], name="unique_venue_seat"
            ),
            models.CheckConstraint(condition=Q(number__gte=1), name="positive_seat_no"),
        ]

    def __str__(self):
        return f"{self.venue}: {self.row}{self.number}"

    def clean(self):
        if self.pk and not self._state.adding:
            previous = Seat.objects.get(pk=self.pk)
            if previous.venue_id != self.venue_id and self.tickets.exists():
                raise ValidationError(
                    {"venue": "Cannot move a seat with ticket history."}
                )


class Category(ValidatedModel):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Event(ValidatedModel):
    title = models.CharField(max_length=160)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="events")
    categories = models.ManyToManyField(Category, related_name="events", blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["starts_at", "id"]
        indexes = [
            models.Index(fields=["starts_at"], name="event_start_idx"),
            models.Index(fields=["venue", "starts_at"], name="event_venue_start_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")), name="event_end_after_start"
            ),
            models.CheckConstraint(condition=Q(price__gte=0), name="nonnegative_price"),
        ]

    def clean(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Must be after starts_at."})
        if self.pk and not self._state.adding:
            previous = Event.objects.get(pk=self.pk)
            if previous.venue_id != self.venue_id and self.bookings.exists():
                raise ValidationError({"venue": "Cannot move an event with bookings."})

    def __str__(self):
        return self.title


class Booking(ValidatedModel):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bookings")
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="bookings")
    seats = models.ManyToManyField(Seat, through="Ticket", related_name="bookings")
    status = models.CharField(
        max_length=9, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"], name="booking_user_created_idx"
            ),
            models.Index(fields=["event", "status"], name="booking_event_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["confirmed", "cancelled"]),
                name="valid_booking_status",
            )
        ]

    def __str__(self):
        return f"Booking {self.pk} ({self.status})"

    def clean(self):
        if self.pk and not self._state.adding:
            previous = Booking.objects.get(pk=self.pk)
            if previous.event_id != self.event_id:
                raise ValidationError({"event": "Cannot change the booked event."})
            if (
                self.status == self.Status.CANCELLED
                and self.tickets.filter(active=True).exists()
            ):
                raise ValidationError({"status": "Release tickets before cancelling."})
            if (
                previous.status == self.Status.CANCELLED
                and self.status != previous.status
            ):
                raise ValidationError(
                    {"status": "Cancelled bookings cannot be reopened."}
                )


class Ticket(ValidatedModel):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="tickets"
    )
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="tickets")
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT, related_name="tickets")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "seat"],
                condition=Q(active=True),
                name="unique_active_event_seat",
            ),
            models.UniqueConstraint(
                fields=["booking", "seat"], name="unique_booking_seat"
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0), name="nonnegative_ticket_price"
            ),
        ]

    def clean(self):
        if self.event_id and self.seat_id:
            if self.seat.venue_id != self.event.venue_id:
                raise ValidationError({"seat": "Seat must belong to the event venue."})
        if self.booking_id:
            if self.event_id != self.booking.event_id:
                raise ValidationError({"event": "Must match the booking event."})
            if self.active and self.booking.status == Booking.Status.CANCELLED:
                raise ValidationError({"active": "Cancelled tickets must be inactive."})

    def __str__(self):
        return f"Ticket {self.pk}: {self.seat}"
