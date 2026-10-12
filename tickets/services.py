from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from tickets.exceptions import Conflict
from tickets.models import Booking, Event, Seat, Ticket


def validate_seats(event, seat_ids, excluding_booking=None):
    if event.starts_at <= timezone.now():
        raise ValidationError({"event": "Reservations close when the event starts."})
    if not seat_ids or len(set(seat_ids)) != len(seat_ids):
        raise ValidationError({"seats": "Provide one or more distinct seat IDs."})
    seats = list(
        Seat.objects.select_for_update().filter(pk__in=seat_ids).order_by("pk")
    )
    if len(seats) != len(seat_ids):
        raise ValidationError({"seats": "One or more seats do not exist."})
    if any(seat.venue_id != event.venue_id for seat in seats):
        raise ValidationError({"seats": "All seats must belong to the event venue."})
    occupied = Ticket.objects.filter(event=event, seat_id__in=seat_ids, active=True)
    if excluding_booking is not None:
        occupied = occupied.exclude(booking=excluding_booking)
    if occupied.exists():
        raise Conflict("One or more seats are already reserved for this event.")
    return seats


@transaction.atomic
def create_booking(user, event, seat_ids):
    # Serialize changes for an event; the partial unique index is a second guard.
    event = Event.objects.select_for_update().get(pk=event.pk)
    seats = validate_seats(event, seat_ids)
    booking = Booking.objects.create(user=user, event=event)
    for seat in seats:
        Ticket.objects.create(
            booking=booking, event=event, seat=seat, price=event.price
        )
    return booking


def locked_booking(booking):
    Event.objects.select_for_update().get(pk=booking.event_id)
    return Booking.objects.select_for_update().get(pk=booking.pk)


def release_seats(booking):
    booking.tickets.filter(active=True).update(active=False)
    if booking.status != Booking.Status.CANCELLED:
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
    return booking


@transaction.atomic
def update_booking(booking, seat_ids=None, status=None):
    booking = locked_booking(booking)
    if status == Booking.Status.CANCELLED:
        if seat_ids is not None:
            raise ValidationError({"seats": "Cannot change seats while cancelling."})
        return release_seats(booking)
    if booking.status == Booking.Status.CANCELLED:
        raise Conflict("Cancelled bookings cannot be reopened or changed.")
    if seat_ids is not None:
        seats = validate_seats(booking.event, seat_ids, excluding_booking=booking)
        # Seat replacement is atomic. Kept seats retain their original price.
        booking.tickets.exclude(seat_id__in=seat_ids).delete()
        existing = set(booking.tickets.values_list("seat_id", flat=True))
        for seat in seats:
            if seat.pk not in existing:
                Ticket.objects.create(
                    booking=booking,
                    event=booking.event,
                    seat=seat,
                    price=booking.event.price,
                )
    return booking


@transaction.atomic
def cancel_booking(booking):
    return release_seats(locked_booking(booking))


@transaction.atomic
def delete_booking(booking):
    booking = locked_booking(booking)
    release_seats(booking)
    booking.delete()
