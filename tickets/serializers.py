from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from tickets import services
from tickets.exceptions import Conflict
from tickets.models import Booking, Category, Event, Seat, Ticket, User, Venue


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, trim_whitespace=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "password",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        password = attrs.get("password")
        if self.instance is None and not password:
            raise serializers.ValidationError({"password": "This field is required."})
        if password:
            candidate = User(
                username=attrs.get("username", getattr(self.instance, "username", "")),
                email=attrs.get("email", getattr(self.instance, "email", "")),
                first_name=attrs.get(
                    "first_name", getattr(self.instance, "first_name", "")
                ),
                last_name=attrs.get(
                    "last_name", getattr(self.instance, "last_name", "")
                ),
            )
            validate_password(password, candidate)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class ProfileSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ["id", "role", "is_active"]

    def validate(self, attrs):
        if {"role", "is_active", "is_staff", "is_superuser"} & self.initial_data.keys():
            raise serializers.ValidationError(
                "Privilege fields cannot be changed here."
            )
        return super().validate(attrs)


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ["id", "name", "address"]


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "venue", "row", "number"]

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = Seat.objects.select_for_update().get(pk=instance.pk)
            venue = validated_data.get("venue", instance.venue)
            if venue.pk != instance.venue_id and instance.tickets.exists():
                raise Conflict(
                    "Cannot move a seat with ticket history to another venue."
                )
            return super().update(instance, validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title", "venue", "categories", "starts_at", "ends_at", "price"]

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({"ends_at": "Must be after starts_at."})
        return attrs

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = Event.objects.select_for_update().get(pk=instance.pk)
            return super().update(instance, validated_data)


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "seat", "event", "price", "active"]
        read_only_fields = fields


class BookingSerializer(serializers.ModelSerializer):
    seats = serializers.ListField(
        child=serializers.IntegerField(min_value=1), write_only=True, required=False
    )
    tickets = TicketSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "event",
            "status",
            "seats",
            "tickets",
            "total",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def validate(self, attrs):
        if "user" in self.initial_data:
            raise serializers.ValidationError(
                {"user": "Ownership is assigned by server."}
            )
        if self.instance is None:
            if not attrs.get("seats"):
                raise serializers.ValidationError(
                    {"seats": "Provide at least one seat."}
                )
            if (
                attrs.get("status", Booking.Status.CONFIRMED)
                != Booking.Status.CONFIRMED
            ):
                raise serializers.ValidationError(
                    {"status": "New bookings are confirmed."}
                )
        elif "event" in attrs and attrs["event"].pk != self.instance.event_id:
            raise serializers.ValidationError(
                {"event": "Cannot change the booked event."}
            )
        return attrs

    def create(self, validated_data):
        return services.create_booking(
            user=self.context["request"].user,
            event=validated_data["event"],
            seat_ids=validated_data["seats"],
        )

    def update(self, instance, validated_data):
        return services.update_booking(
            instance,
            seat_ids=validated_data.get("seats"),
            status=validated_data.get("status"),
        )

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total(self, instance):
        return f"{sum(ticket.price for ticket in instance.tickets.all()):.2f}"
