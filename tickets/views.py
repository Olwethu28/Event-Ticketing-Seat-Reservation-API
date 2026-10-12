from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from tickets import services
from tickets.models import Booking, Category, Event, Seat, User, Venue
from tickets.permissions import AdminOnly, AdminOrReadOnly, is_admin
from tickets.serializers import (
    BookingSerializer,
    CategorySerializer,
    EventSerializer,
    ProfileSerializer,
    SeatSerializer,
    UserSerializer,
    VenueSerializer,
)


class RegisterView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ProfileSerializer


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOnly]
    serializer_class = UserSerializer
    queryset = User.objects.order_by("id")


class VenueViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOrReadOnly]
    serializer_class = VenueSerializer
    queryset = Venue.objects.all()


class SeatViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOrReadOnly]
    serializer_class = SeatSerializer
    queryset = Seat.objects.select_related("venue")

    def get_queryset(self):
        queryset = super().get_queryset()
        venue = self.request.query_params.get("venue")
        if venue:
            queryset = (
                queryset.filter(venue_id=venue)
                if venue.isdecimal()
                else queryset.none()
            )
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOrReadOnly]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOrReadOnly]
    serializer_class = EventSerializer
    queryset = Event.objects.select_related("venue").prefetch_related("categories")

    def get_queryset(self):
        queryset = super().get_queryset()
        venue = self.request.query_params.get("venue")
        if venue:
            queryset = (
                queryset.filter(venue_id=venue)
                if venue.isdecimal()
                else queryset.none()
            )
        if self.request.query_params.get("upcoming") == "true":
            queryset = queryset.filter(starts_at__gt=timezone.now())
        return queryset

    @extend_schema(responses=SeatSerializer(many=True))
    @action(detail=True, methods=["get"], pagination_class=None)
    def available_seats(self, request, pk=None):
        event = self.get_object()
        seats = event.venue.seats.exclude(
            pk__in=event.tickets.filter(active=True).values("seat_id")
        )
        return Response(SeatSerializer(seats, many=True).data)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    queryset = Booking.objects.select_related("event", "user").prefetch_related(
        "tickets"
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        return (
            queryset
            if is_admin(self.request.user)
            else queryset.filter(user=self.request.user)
        )

    @extend_schema(request=None, responses=BookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = services.cancel_booking(self.get_object())
        return Response(self.get_serializer(booking).data)

    def perform_destroy(self, instance):
        services.delete_booking(instance)
