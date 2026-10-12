from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from tickets.views import (
    BookingViewSet,
    CategoryViewSet,
    EventViewSet,
    MeView,
    RegisterView,
    SeatViewSet,
    UserViewSet,
    VenueViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("venues", VenueViewSet)
router.register("seats", SeatViewSet)
router.register("categories", CategoryViewSet)
router.register("events", EventViewSet)
router.register("bookings", BookingViewSet)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
