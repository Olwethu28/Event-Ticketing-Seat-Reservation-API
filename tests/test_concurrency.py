from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from tickets.exceptions import Conflict
from tickets.models import Booking, Ticket
from tickets.services import create_booking


@pytest.mark.django_db(transaction=True)
def test_concurrent_requests_can_only_reserve_a_seat_once(
    user, other_user, event, seats
):
    assert (
        connection.vendor == "postgresql"
    ), "Concurrency must be tested on PostgreSQL."
    barrier = Barrier(2)

    def reserve(customer):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                create_booking(customer, event, [seats[0].pk])
                return "created"
            except Conflict:
                return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(reserve, [user, other_user]))
    assert sorted(results) == ["conflict", "created"]
    assert Booking.objects.count() == Ticket.objects.filter(active=True).count() == 1
