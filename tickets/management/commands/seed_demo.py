import os
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from tickets.models import Category, Event, Seat, User, Venue


class Command(BaseCommand):
    help = "Create an idempotent fictional catalog and two demo accounts."

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.environ.get("DEMO_PASSWORD")
        if not password or len(password) < 12:
            raise CommandError("Set DEMO_PASSWORD to at least 12 characters.")
        for username, role in [
            ("demo_admin", User.Role.ADMIN),
            ("demo_guest", User.Role.STANDARD),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@halcyon.example", "role": role},
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
        venue, _ = Venue.objects.get_or_create(
            name="Aurora Demo Hall",
            defaults={"address": "44 Imaginary Crescent, Fictional City"},
        )
        for row in ["A", "B"]:
            for number in range(1, 6):
                Seat.objects.get_or_create(venue=venue, row=row, number=number)
        category, _ = Category.objects.get_or_create(name="Fictional Music")
        starts_at = timezone.now().replace(microsecond=0) + timedelta(days=30)
        event, _ = Event.objects.get_or_create(
            title="The Imaginary Orchestra",
            venue=venue,
            defaults={
                "starts_at": starts_at,
                "ends_at": starts_at + timedelta(hours=2),
                "price": "25.00",
            },
        )
        event.categories.add(category)
        self.stdout.write(
            self.style.SUCCESS(
                "Fictional demo seeded: demo_admin, demo_guest; "
                f"event={event.pk}, venue={venue.pk}. Existing passwords unchanged."
            )
        )
