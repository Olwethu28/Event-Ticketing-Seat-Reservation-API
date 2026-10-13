import pytest

from tests.conftest import PASSWORD
from tickets.models import User

pytestmark = pytest.mark.django_db


def test_registration_hashes_password_and_defaults_to_standard(api):
    response = api.post(
        "/api/auth/register/",
        {"username": "new_guest", "password": PASSWORD, "email": "new@halcyon.example"},
        format="json",
    )
    assert response.status_code == 201
    assert "password" not in response.data
    user = User.objects.get(username="new_guest")
    assert user.check_password(PASSWORD)
    assert user.role == "standard"
    assert not user.is_staff and not user.is_superuser


@pytest.mark.parametrize("field", ["role", "is_active", "is_staff", "is_superuser"])
def test_registration_rejects_privilege_fields(api, field):
    response = api.post(
        "/api/auth/register/",
        {"username": "escalation", "password": PASSWORD, field: "admin"},
        format="json",
    )
    assert response.status_code == 400
    assert not User.objects.filter(username="escalation").exists()


@pytest.mark.parametrize("password", ["123", "password", "123456789123"])
def test_weak_password_rejected(api, password):
    response = api.post(
        "/api/auth/register/",
        {"username": "new_guest", "password": password},
        format="json",
    )
    assert response.status_code == 400


def test_duplicate_username_and_missing_password(api, user):
    duplicate = api.post(
        "/api/auth/register/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    missing = api.post("/api/auth/register/", {"username": "missing"}, format="json")
    assert duplicate.status_code == missing.status_code == 400


def test_jwt_login_refresh_and_me(api, user):
    response = api.post(
        "/api/auth/token/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    refresh = api.post(
        "/api/auth/token/refresh/", {"refresh": response.data["refresh"]}, format="json"
    )
    assert refresh.status_code == 200
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.data['access']}")
    assert api.get("/api/auth/me/").data["id"] == user.pk


def test_invalid_password_token_and_inactive_user(api, user):
    invalid_login = api.post(
        "/api/auth/token/",
        {"username": user.username, "password": "wrong"},
        format="json",
    )
    invalid_refresh = api.post(
        "/api/auth/token/refresh/", {"refresh": "invalid"}, format="json"
    )
    assert invalid_login.status_code == invalid_refresh.status_code == 401
    user.is_active = False
    user.save()
    assert (
        api.post(
            "/api/auth/token/",
            {"username": user.username, "password": PASSWORD},
            format="json",
        ).status_code
        == 401
    )
    api.credentials(HTTP_AUTHORIZATION="Bearer invalid")
    assert api.get("/api/auth/me/").status_code == 401


def test_me_update_and_password_change(client, user):
    response = client.patch(
        "/api/auth/me/",
        {"first_name": "Fictional", "password": "Changed-Fictional-0448!"},
        format="json",
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Fictional"
    assert user.check_password("Changed-Fictional-0448!")
    full = client.put(
        "/api/auth/me/", {"username": user.username, "last_name": "Demo"}, format="json"
    )
    assert full.status_code == 200


def test_me_cannot_change_role(client):
    assert (
        client.patch("/api/auth/me/", {"role": "admin"}, format="json").status_code
        == 400
    )


@pytest.mark.parametrize(
    "resource", ["venues", "seats", "categories", "events", "bookings", "users"]
)
def test_anonymous_cannot_read_resources(api, resource):
    assert api.get(f"/api/{resource}/").status_code == 401


def test_me_requires_authentication(api):
    assert api.get("/api/auth/me/").status_code == 401


def test_standard_user_cannot_manage_users(client, user):
    assert client.get("/api/users/").status_code == 403
    assert client.patch(f"/api/users/{user.pk}/", {"role": "admin"}).status_code == 403


def test_admin_user_crud(admin_client):
    response = admin_client.post(
        "/api/users/", {"username": "managed", "password": PASSWORD}, format="json"
    )
    assert response.status_code == 201
    pk = response.data["id"]
    assert admin_client.get("/api/users/").status_code == 200
    assert admin_client.get(f"/api/users/{pk}/").status_code == 200
    assert (
        admin_client.patch(
            f"/api/users/{pk}/", {"role": "admin"}, format="json"
        ).status_code
        == 200
    )
    assert (
        admin_client.put(
            f"/api/users/{pk}/",
            {"username": "renamed", "role": "standard"},
            format="json",
        ).status_code
        == 200
    )
    assert admin_client.delete(f"/api/users/{pk}/").status_code == 204
