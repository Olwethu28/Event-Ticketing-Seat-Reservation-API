from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from tickets.models import Booking, Event, Seat, Ticket, Venue
from tickets.services import create_booking

pytestmark = pytest.mark.django_db


def test_booking_crud_and_price_snapshot(client, event, seats):
    response = client.post(
        "/api/bookings/", {"event": event.pk, "seats": [seats[0].pk]}, format="json"
    )
    assert response.status_code == 201, response.data
    pk = response.data["id"]
    assert response.data["total"] == "25.00"
    assert response.data["tickets"][0]["active"] is True
    assert client.get("/api/bookings/").data["count"] == 1
    assert client.get(f"/api/bookings/{pk}/").status_code == 200
    event.price = "30.00"
    event.save()
    response = client.patch(
        f"/api/bookings/{pk}/", {"seats": [s.pk for s in seats[:2]]}, format="json"
    )
    assert response.status_code == 200
    assert response.data["total"] == "55.00"
    response = client.put(
        f"/api/bookings/{pk}/",
        {"event": event.pk, "seats": [seats[1].pk], "status": "confirmed"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["total"] == "30.00"
    assert client.delete(f"/api/bookings/{pk}/").status_code == 204
    assert not Ticket.objects.filter(booking_id=pk).exists()
    assert client.get(f"/api/events/{event.pk}/available_seats/").data == [
        {"id": s.pk, "venue": s.venue_id, "row": s.row, "number": s.number}
        for s in seats
    ]


def test_double_booking_is_rejected_atomically(client, booking, event, seats):
    response = client.post(
        "/api/bookings/",
        {"event": event.pk, "seats": [s.pk for s in seats]},
        format="json",
    )
    assert response.status_code == 409
    assert response.data["error"]["code"] == "conflict"
    assert Booking.objects.count() == Ticket.objects.count() == 1


@pytest.mark.parametrize("method", ["action", "patch", "put"])
def test_cancellation_is_idempotent_and_releases_seats(client, booking, seats, method):
    url = f"/api/bookings/{booking.pk}/"
    if method == "action":
        response = client.post(f"{url}cancel/")
    elif method == "put":
        response = client.put(
            url, {"event": booking.event_id, "status": "cancelled"}, format="json"
        )
    else:
        response = client.patch(url, {"status": "cancelled"}, format="json")
    assert response.status_code == 200
    assert response.data["status"] == "cancelled"
    assert response.data["tickets"][0]["active"] is False
    assert client.post(f"{url}cancel/").status_code == 200
    response = client.post(
        "/api/bookings/",
        {"event": booking.event_id, "seats": [seats[0].pk]},
        format="json",
    )
    assert response.status_code == 201
    assert Ticket.objects.count() == 2
    assert Ticket.objects.filter(active=True).count() == 1
    assert Booking.objects.get(pk=booking.pk).seats.count() == 1
    assert client.patch(url, {"status": "confirmed"}, format="json").status_code == 409
    assert client.patch(url, {"seats": [seats[1].pk]}, format="json").status_code == 409


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete", "cancel"])
def test_other_users_cannot_access_booking(booking, other_user, method):
    client = APIClient()
    client.force_authenticate(other_user)
    url = f"/api/bookings/{booking.pk}/"
    if method == "cancel":
        response = client.post(f"{url}cancel/")
    else:
        response = getattr(client, method)(url, {}, format="json")
    assert response.status_code == 404
    assert client.get("/api/bookings/").data["count"] == 0
    booking.refresh_from_db()
    assert booking.status == "confirmed"


def test_admin_can_manage_all_bookings(admin_client, booking):
    assert admin_client.get("/api/bookings/").data["count"] == 1
    assert admin_client.get(f"/api/bookings/{booking.pk}/").status_code == 200
    assert admin_client.post(f"/api/bookings/{booking.pk}/cancel/").status_code == 200
    assert admin_client.delete(f"/api/bookings/{booking.pk}/").status_code == 204


@pytest.mark.parametrize("seat_ids", [[], [999999], [0], [-1], ["bad"]])
def test_invalid_seat_ids(client, event, seat_ids):
    response = client.post(
        "/api/bookings/", {"event": event.pk, "seats": seat_ids}, format="json"
    )
    assert response.status_code == 400
    assert not Booking.objects.exists()


def test_duplicate_and_wrong_venue_seats(client, event, seats):
    duplicate = client.post(
        "/api/bookings/", {"event": event.pk, "seats": [seats[0].pk] * 2}, format="json"
    )
    assert duplicate.status_code == 400
    other = Venue.objects.create(name="Other Fictional Hall", address="Demo Lane")
    seat = Seat.objects.create(venue=other, row="A", number=1)
    response = client.post(
        "/api/bookings/", {"event": event.pk, "seats": [seat.pk]}, format="json"
    )
    assert response.status_code == 400
    assert not Booking.objects.exists()


def test_booking_owner_cannot_be_spoofed(client, other_user, event, seats):
    response = client.post(
        "/api/bookings/",
        {"event": event.pk, "seats": [seats[0].pk], "user": other_user.pk},
        format="json",
    )
    assert response.status_code == 400


def test_missing_seats_and_cancelled_creation(client, event, seats):
    assert (
        client.post("/api/bookings/", {"event": event.pk}, format="json").status_code
        == 400
    )
    assert (
        client.post(
            "/api/bookings/",
            {"event": event.pk, "seats": [seats[0].pk], "status": "cancelled"},
            format="json",
        ).status_code
        == 400
    )


def test_started_event_rejects_booking(client, event, seats):
    event.starts_at = timezone.now() - timedelta(hours=2)
    event.ends_at = timezone.now() - timedelta(hours=1)
    event.save()
    assert (
        client.post(
            "/api/bookings/", {"event": event.pk, "seats": [seats[0].pk]}, format="json"
        ).status_code
        == 400
    )


def test_cannot_change_event_or_cancel_and_replace_seats(client, booking, seats):
    event = Event.objects.create(
        title="Another Fictional Show",
        venue=booking.event.venue,
        starts_at=booking.event.starts_at,
        ends_at=booking.event.ends_at,
        price="20.00",
    )
    assert (
        client.patch(
            f"/api/bookings/{booking.pk}/", {"event": event.pk}, format="json"
        ).status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/bookings/{booking.pk}/",
            {"status": "cancelled", "seats": [seats[1].pk]},
            format="json",
        ).status_code
        == 400
    )


def test_replacement_conflict_preserves_original_seats(client, user, booking, seats):
    create_booking(user, booking.event, [seats[1].pk])
    response = client.patch(
        f"/api/bookings/{booking.pk}/", {"seats": [seats[1].pk]}, format="json"
    )
    assert response.status_code == 409
    assert list(booking.seats.values_list("id", flat=True)) == [seats[0].pk]


def test_same_seat_can_be_booked_for_different_events(client, booking, seats):
    event = Event.objects.create(
        title="Second Fictional Show",
        venue=booking.event.venue,
        starts_at=booking.event.starts_at + timedelta(days=1),
        ends_at=booking.event.ends_at + timedelta(days=1),
        price="20.00",
    )
    assert (
        client.post(
            "/api/bookings/", {"event": event.pk, "seats": [seats[0].pk]}, format="json"
        ).status_code
        == 201
    )


def test_availability_changes_with_reservation_and_cancellation(client, booking, seats):
    url = f"/api/events/{booking.event_id}/available_seats/"
    assert {seat["id"] for seat in client.get(url).data} == {s.pk for s in seats[1:]}
    client.post(f"/api/bookings/{booking.pk}/cancel/")
    assert {seat["id"] for seat in client.get(url).data} == {s.pk for s in seats}
