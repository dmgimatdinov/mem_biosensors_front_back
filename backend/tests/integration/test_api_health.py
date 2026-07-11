import pytest


@pytest.mark.integration
class TestAPIHealth:

    def test_health_endpoint(self, api_client):
        """GET /api/health возвращает 200 с правильным JSON."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data

    def test_docs_endpoint_accessible(self, api_client):
        """GET /docs возвращает 200 (Swagger UI доступен)."""
        response = api_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_accessible(self, api_client):
        """GET /redoc возвращает 200."""
        response = api_client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json(self, api_client):
        """GET /openapi.json возвращает валидную OpenAPI-схему."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
