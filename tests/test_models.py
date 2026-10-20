from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from tickets.models import Booking, Category, Event, Seat, Ticket, User, Venue
from tickets.services import cancel_booking

pytestmark = pytest.mark.django_db


def test_model_relationships_and_strings(user, venue, seats, event, category, booking):
    ticket = booking.tickets.get()
    assert event.venue == venue
    assert event.categories.get() == category
    assert booking.user == user
    assert booking.seats.get() == seats[0]
    assert ticket.booking == booking and ticket.event == event
    assert str(venue) == venue.name
    assert str(category) == category.name
    assert str(event) == event.title
    assert str(seats[0]) == f"{venue}: A1"
    assert str(booking).startswith("Booking ")
    assert str(ticket).startswith("Ticket ")


def test_invalid_event_duration_price_and_seat_number(venue, event):
    event.ends_at = event.starts_at
    with pytest.raises(ValidationError):
        event.save()
    event.ends_at = event.starts_at + timedelta(hours=1)
    event.price = "-1.00"
    with pytest.raises(ValidationError):
        event.save()
    with pytest.raises(ValidationError):
        Seat.objects.create(venue=venue, row="A", number=0)
    with pytest.raises(ValidationError):
        Venue.objects.create(name="", address="Demo Lane")


def test_unique_category_and_seat_constraints(category, seats):
    with pytest.raises(ValidationError):
        Category.objects.create(name=category.name)
    with pytest.raises(ValidationError):
        Seat.objects.create(venue=seats[0].venue, row="A", number=1)


def test_ticket_cross_model_validation(user, venue, event, seats, booking):
    other = Venue.objects.create(name="Another Demo Hall", address="Fictional Lane")
    foreign_seat = Seat.objects.create(venue=other, row="A", number=1)
    with pytest.raises(ValidationError, match="event venue"):
        Ticket.objects.create(
            booking=booking, event=event, seat=foreign_seat, price="25.00"
        )
    other_event = Event.objects.create(
        title="Other Demo Show",
        venue=venue,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        price="25.00",
    )
    with pytest.raises(ValidationError, match="booking event"):
        Ticket.objects.create(
            booking=booking, event=other_event, seat=seats[1], price="25.00"
        )
    cancelled = Booking.objects.create(user=user, event=event, status="cancelled")
    with pytest.raises(ValidationError, match="inactive"):
        Ticket.objects.create(
            booking=cancelled, event=event, seat=seats[1], price="25.00"
        )


def test_partial_unique_constraint_even_for_bulk_writes(user, booking, event, seats):
    other = Booking.objects.create(user=user, event=event)
    with pytest.raises(IntegrityError), transaction.atomic():
        Ticket.objects.bulk_create(
            [Ticket(booking=other, event=event, seat=seats[0], price="25.00")]
        )
    assert Ticket.objects.count() == 1


def test_booking_and_ticket_check_constraints(user, event, seats):
    with pytest.raises(IntegrityError), transaction.atomic():
        Booking.objects.bulk_create([Booking(user=user, event=event, status="invalid")])
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.bulk_create([User(username="invalid", role="invalid")])
    with pytest.raises(IntegrityError), transaction.atomic():
        Seat.objects.bulk_create([Seat(venue=event.venue, row="Z", number=0)])
    with pytest.raises(IntegrityError), transaction.atomic():
        Event.objects.bulk_create(
            [
                Event(
                    venue=event.venue,
                    title="Bad Demo Event",
                    starts_at=event.starts_at,
                    ends_at=event.starts_at,
                    price="-1.00",
                )
            ]
        )


def test_venue_move_and_booking_lifecycle_guards(booking, seats):
    other = Venue.objects.create(name="Another Demo Hall", address="Fictional Lane")
    event = booking.event
    event.venue = other
    with pytest.raises(ValidationError, match="Cannot move"):
        event.save()
    seat = seats[0]
    seat.venue = other
    with pytest.raises(ValidationError, match="Cannot move"):
        seat.save()
    booking.status = "cancelled"
    with pytest.raises(ValidationError, match="Release tickets"):
        booking.save()
    booking = cancel_booking(booking)
    booking.status = "confirmed"
    with pytest.raises(ValidationError, match="cannot be reopened"):
        booking.save()
    booking.refresh_from_db()
    other_event = Event.objects.create(
        title="Other Demo Show",
        venue=other,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        price="25.00",
    )
    booking.event = other_event
    with pytest.raises(ValidationError, match="Cannot change"):
        booking.save()


def test_ticket_nonnegative_price_and_unique_booking_seat(booking, seats):
    with pytest.raises(ValidationError):
        Ticket.objects.create(
            booking=booking, event=booking.event, seat=seats[1], price="-1.00"
        )
    with pytest.raises(ValidationError):
        Ticket.objects.create(
            booking=booking,
            event=booking.event,
            seat=seats[0],
            price="25.00",
            active=False,
        )
