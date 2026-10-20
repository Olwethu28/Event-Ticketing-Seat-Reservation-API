import json
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, OperationalError
from django.test import RequestFactory
from rest_framework.exceptions import ValidationError

from tickets.exceptions import api_exception_handler, handler500

pytestmark = pytest.mark.django_db


def assert_error(response, expected_status, path):
    data = json.loads(response.content)
    assert response.status_code == expected_status
    error = data["error"]
    assert set(error) == {"status", "code", "message", "details", "path", "timestamp"}
    assert error["status"] == expected_status
    assert error["path"] == path
    assert error["timestamp"]
    return error


def test_health_success_is_public(api):
    api.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
    response = api.get("/health/")
    assert response.status_code == 200
    assert response.data["status"] == "ok"
    assert response.data["database"] == "connected"
    assert response.data["service"] == "halcyon-ticketing-api"
    assert response.data["uptime_seconds"] >= 0


def test_health_database_down_returns_503(api):
    with patch(
        "tickets.health.connection.cursor", side_effect=OperationalError("db down")
    ):
        response = api.get("/health/")
    assert response.status_code == 503
    assert response.data["status"] == "degraded"
    assert response.data["database"] == "unavailable"
    assert "db down" not in str(response.data)


def test_health_unexpected_probe_result(api):
    with patch("tickets.health.connection.cursor") as cursor:
        cursor.return_value.__enter__.return_value.fetchone.return_value = (0,)
        assert api.get("/health/").status_code == 503


def test_auth_validation_and_not_found_error_envelopes(api, client):
    assert_error(api.get("/api/bookings/"), 401, "/api/bookings/")
    error = assert_error(
        api.post("/api/auth/register/", {}, format="json"), 400, "/api/auth/register/"
    )
    assert "username" in error["details"]
    assert_error(client.get("/api/bookings/999999/"), 404, "/api/bookings/999999/")


def test_json_404_for_unknown_non_api_route(api, settings):
    settings.DEBUG = False
    error = assert_error(api.get("/nonexistent/"), 404, "/nonexistent/")
    assert error["code"] == "not_found"


def test_json_500_handler():
    response = handler500(RequestFactory().get("/unexpected/"))
    assert_error(response, 500, "/unexpected/")


@pytest.mark.parametrize(
    "exc,expected",
    [
        (ValidationError({"field": "invalid"}), 400),
        (DjangoValidationError({"field": "invalid"}), 400),
        (DjangoValidationError("invalid"), 400),
        (IntegrityError("private database details"), 409),
        (RuntimeError("private internal details"), 500),
    ],
)
def test_exception_handler_normalises_errors(exc, expected):
    response = api_exception_handler(
        exc, {"request": RequestFactory().get("/failure/")}
    )
    assert response.status_code == expected
    assert response.data["error"]["path"] == "/failure/"
    assert "private" not in str(response.data)


def test_unhandled_api_failure_is_normalised(client, event, seats):
    with patch(
        "tickets.views.services.create_booking", side_effect=RuntimeError("private")
    ):
        response = client.post(
            "/api/bookings/", {"event": event.pk, "seats": [seats[0].pk]}, format="json"
        )
    error = assert_error(response, 500, "/api/bookings/")
    assert "private" not in str(error)


def test_openapi_and_swagger_are_public(api):
    schema = api.get("/api/schema/?format=json")
    assert schema.status_code == 200
    paths = schema.json()["paths"]
    assert "/api/bookings/" in paths
    assert "/api/auth/register/" in paths
    assert "/health/" in paths
    assert api.get("/api/docs/").status_code == 200


def test_malformed_json_and_disallowed_method(api):
    response = api.post(
        "/api/auth/register/", "{bad-json", content_type="application/json"
    )
    assert_error(response, 400, "/api/auth/register/")
    assert_error(api.delete("/api/auth/register/"), 405, "/api/auth/register/")
