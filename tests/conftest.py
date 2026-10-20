import os
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

os.environ.setdefault(
    "DJANGO_SECRET_KEY", "test-only-fictional-key-at-least-thirty-two-characters"
)
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

PASSWORD = "Fictional-Demo-0448!"


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="guest", password=PASSWORD, email="guest@halcyon.example"
    )


@pytest.fixture
def other_user(db, django_user_model):
    return django_user_model.objects.create_user(username="other", password=PASSWORD)


@pytest.fixture
def admin_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="operator", password=PASSWORD, role="admin"
    )


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def client(user):
    api = APIClient()
    response = api.post(
        "/api/auth/token/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api


@pytest.fixture
def admin_client(admin_user):
    api = APIClient()
    response = api.post(
        "/api/auth/token/",
        {"username": admin_user.username, "password": PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api


@pytest.fixture
def venue(db):
    from tickets.models import Venue

    return Venue.objects.create(name="Imaginary Hall", address="44 Fictional Road")


@pytest.fixture
def seats(venue):
    from tickets.models import Seat

    return [Seat.objects.create(venue=venue, row="A", number=n) for n in range(1, 4)]


@pytest.fixture
def category(db):
    from tickets.models import Category

    return Category.objects.create(name="Demo Music")


@pytest.fixture
def event(venue, category):
    from tickets.models import Event

    start = timezone.now() + timedelta(days=10)
    event = Event.objects.create(
        title="Fictional Gala",
        venue=venue,
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        price="25.00",
    )
    event.categories.add(category)
    return event


@pytest.fixture
def booking(user, event, seats):
    from tickets.services import create_booking

    return create_booking(user, event, [seats[0].pk])
