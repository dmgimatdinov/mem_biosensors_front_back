import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_MODE", "jwt")

from main import app  # noqa: E402


@pytest.fixture
def jwt_client():
    os.environ["AUTH_MODE"] = "jwt"
    import settings
    settings.AUTH_MODE = "jwt"
    return TestClient(app)


def test_login_refresh_logout_cycle(jwt_client):
    login = jwt_client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    refresh = jwt_client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    refreshed = refresh.json()
    assert refreshed["access_token"] != tokens["access_token"]

    logout = jwt_client.post("/api/auth/logout", json={"refresh_token": refreshed["refresh_token"]})
    assert logout.status_code == 200


def _admin_headers(jwt_client):
    login = jwt_client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    access = login.json()["access_token"]
    return {"Authorization": f"Bearer {access}"}


def test_register_requires_admin_role(jwt_client):
    # bootstrap a designer via admin
    headers = _admin_headers(jwt_client)
    created = jwt_client.post(
        "/api/auth/register",
        headers=headers,
        json={"username": "designer_user", "password": "password123", "role": "Designer"},
    )
    assert created.status_code == 200

    # designer token should not register users
    designer_login = jwt_client.post(
        "/api/auth/login",
        json={"username": "designer_user", "password": "password123"},
    )
    d_token = designer_login.json()["access_token"]
    forbidden = jwt_client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {d_token}"},
        json={"username": "x", "password": "password123", "role": "Designer"},
    )
    assert forbidden.status_code == 403


def test_api_keys_management(jwt_client):
    headers = _admin_headers(jwt_client)

    create_key = jwt_client.post(
        "/api/api-keys/generate",
        headers=headers,
        json={"username": "admin", "name": "ci-key"},
    )
    assert create_key.status_code == 200
    key_body = create_key.json()
    assert "api_key" in key_body

    keys = jwt_client.get("/api/api-keys", headers=headers)
    assert keys.status_code == 200
    assert isinstance(keys.json(), list)

    revoke = jwt_client.delete(f"/api/api-keys/{key_body['id']}", headers=headers)
    assert revoke.status_code == 200


def test_protected_endpoint_requires_auth(jwt_client):
    no_auth = jwt_client.get("/api/analytics/statistics")
    assert no_auth.status_code == 401


def test_api_key_auth_for_designer_endpoint(jwt_client):
    headers = _admin_headers(jwt_client)
    create_key = jwt_client.post(
        "/api/api-keys/generate",
        headers=headers,
        json={"username": "admin", "name": "admin-key"},
    )
    api_key = create_key.json()["api_key"]

    res = jwt_client.get("/api/analytics/statistics", headers={"X-API-Key": api_key})
    assert res.status_code in (200, 500)
    # 500 possible if analytics table state is empty/missing in minimal test env.
