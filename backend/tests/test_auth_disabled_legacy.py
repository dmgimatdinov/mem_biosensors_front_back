import os

from fastapi.testclient import TestClient

from main import app


def test_disabled_auth_keeps_legacy_open_access():
    os.environ["AUTH_MODE"] = "disabled"
    import settings
    settings.AUTH_MODE = "disabled"

    client = TestClient(app)
    response = client.get("/api/analytics/statistics")
    # In disabled mode endpoint should pass auth gate; business logic may still return 500
    assert response.status_code != 401
    assert response.status_code != 403
