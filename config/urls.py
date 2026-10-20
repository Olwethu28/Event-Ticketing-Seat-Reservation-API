from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from tickets.health import HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthView.as_view(), name="health"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/", include("tickets.urls")),
]

handler404 = "tickets.exceptions.handler404"
handler500 = "tickets.exceptions.handler500"
