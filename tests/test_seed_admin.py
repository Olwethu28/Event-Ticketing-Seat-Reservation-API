from io import StringIO

import pytest
from django.contrib import admin
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory

from tickets.admin import ReservationAdmin
from tickets.models import Booking, Category, Event, Seat, User, Venue

pytestmark = pytest.mark.django_db


def test_seed_demo_is_idempotent_and_uses_fictional_data(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "Fictional-Seed-0448!")
    output = StringIO()
    call_command("seed_demo", stdout=output)
    password = User.objects.get(username="demo_admin").password
    monkeypatch.setenv("DEMO_PASSWORD", "Another-Seed-0448!")
    call_command("seed_demo", stdout=output)
    assert User.objects.count() == 2
    assert (
        Venue.objects.count() == Event.objects.count() == Category.objects.count() == 1
    )
    assert Seat.objects.count() == 10
    assert User.objects.get(username="demo_admin").role == "admin"
    assert User.objects.get(username="demo_guest").role == "standard"
    assert User.objects.get(username="demo_admin").password == password
    assert all(user.email.endswith(".example") for user in User.objects.all())
    assert "Fictional demo seeded" in output.getvalue()


@pytest.mark.parametrize("password", ["", "short"])
def test_seed_requires_explicit_demo_password(monkeypatch, password):
    monkeypatch.setenv("DEMO_PASSWORD", password)
    with pytest.raises(CommandError):
        call_command("seed_demo")
    assert not User.objects.exists()


def test_reservations_are_read_only_in_django_admin(admin_user):
    request = RequestFactory().get("/admin/")
    request.user = admin_user
    model_admin = ReservationAdmin(Booking, admin.site)
    assert model_admin.has_add_permission(request) is False
    assert model_admin.has_change_permission(request) is False
    assert model_admin.has_delete_permission(request) is False
