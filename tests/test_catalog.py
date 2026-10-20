from datetime import timedelta

import pytest
from django.utils import timezone

from tickets.models import Venue

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("resource", ["venues", "seats", "categories", "events"])
def test_catalog_admin_crud_and_standard_permissions(
    admin_client, client, venue, category, resource
):
    start = timezone.now() + timedelta(days=20)
    payloads = {
        "venues": {"name": "Fictional Arena", "address": "22 Imaginary Lane"},
        "seats": {"venue": venue.pk, "row": "B", "number": 9},
        "categories": {"name": "Fictional Theatre"},
        "events": {
            "title": "Demo Performance",
            "venue": venue.pk,
            "categories": [category.pk],
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=1)).isoformat(),
            "price": "12.50",
        },
    }
    payload = payloads[resource]
    url = f"/api/{resource}/"
    assert client.post(url, payload, format="json").status_code == 403
    response = admin_client.post(url, payload, format="json")
    assert response.status_code == 201, response.data
    detail = f"{url}{response.data['id']}/"
    assert client.get(url).status_code == 200
    assert client.get(detail).status_code == 200
    assert admin_client.get(detail).status_code == 200
    assert client.put(detail, payload, format="json").status_code == 403
    assert client.patch(detail, payload, format="json").status_code == 403
    assert client.delete(detail).status_code == 403
    assert admin_client.patch(detail, payload, format="json").status_code == 200
    assert admin_client.put(detail, payload, format="json").status_code == 200
    assert admin_client.delete(detail).status_code == 204


def test_catalog_validation(admin_client, venue, event):
    assert (
        admin_client.post(
            "/api/seats/", {"venue": venue.pk, "row": "A", "number": 0}, format="json"
        ).status_code
        == 400
    )
    assert (
        admin_client.patch(
            f"/api/events/{event.pk}/", {"price": "-1.00"}, format="json"
        ).status_code
        == 400
    )
    assert (
        admin_client.patch(
            f"/api/events/{event.pk}/",
            {"ends_at": event.starts_at.isoformat()},
            format="json",
        ).status_code
        == 400
    )
    assert (
        admin_client.post("/api/venues/", {"name": ""}, format="json").status_code
        == 400
    )


def test_unique_seat_and_category(admin_client, seats, category):
    seat = seats[0]
    assert (
        admin_client.post(
            "/api/seats/",
            {"venue": seat.venue_id, "row": seat.row, "number": seat.number},
            format="json",
        ).status_code
        == 400
    )
    assert (
        admin_client.post(
            "/api/categories/", {"name": category.name}, format="json"
        ).status_code
        == 400
    )


def test_venue_and_upcoming_filters(client, event, seats):
    venue = event.venue_id
    assert client.get(f"/api/events/?venue={venue}&upcoming=true").data["count"] == 1
    assert client.get("/api/events/?venue=999999").data["count"] == 0
    assert client.get("/api/events/?venue=invalid").data["count"] == 0
    assert client.get(f"/api/seats/?venue={venue}").data["count"] == len(seats)
    assert client.get("/api/seats/?venue=invalid").data["count"] == 0


def test_protected_deletion_and_venue_moves(admin_client, booking, seats):
    other = Venue.objects.create(name="Other Fictional Hall", address="Demo Lane")
    assert (
        admin_client.delete(f"/api/venues/{booking.event.venue_id}/").status_code == 409
    )
    assert admin_client.delete(f"/api/events/{booking.event_id}/").status_code == 409
    assert admin_client.delete(f"/api/seats/{seats[0].pk}/").status_code == 409
    assert admin_client.delete(f"/api/users/{booking.user_id}/").status_code == 409
    assert (
        admin_client.patch(
            f"/api/events/{booking.event_id}/", {"venue": other.pk}, format="json"
        ).status_code
        == 400
    )
    assert (
        admin_client.patch(
            f"/api/seats/{seats[0].pk}/", {"venue": other.pk}, format="json"
        ).status_code
        == 409
    )


def test_unbooked_catalog_can_move(admin_client, event, seats):
    other = Venue.objects.create(name="Other Fictional Hall", address="Demo Lane")
    assert (
        admin_client.patch(
            f"/api/seats/{seats[0].pk}/", {"venue": other.pk}, format="json"
        ).status_code
        == 200
    )
    assert (
        admin_client.patch(
            f"/api/events/{event.pk}/", {"venue": other.pk}, format="json"
        ).status_code
        == 200
    )
