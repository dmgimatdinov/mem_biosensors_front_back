import pytest

@pytest.mark.integration
class TestCORS:

    def test_cors_preflight_localhost_3000(self, api_client):
        print("Running test_cors_preflight_localhost_3000")
        """OPTIONS с Origin: http://localhost:3000 → разрешено."""
        response = api_client.options(
            "/api/analytes",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        assert response.status_code == 200
        assert "http://localhost:3000" in response.headers.get("access-control-allow-origin", "")

    @pytest.mark.parametrize("origin", [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ])
    def test_cors_allowed_origins(self, api_client, origin):
        """Запросы с разрешённых origin проходят."""
        response = api_client.get(
            "/api/health",
            headers={"Origin": origin}
        )
        assert response.status_code == 200
        assert origin in response.headers.get("access-control-allow-origin", "")

    def test_cors_disallowed_origin(self, api_client):
        """Запрос с неразрешённого origin не получает разрешающих заголовков."""
        response = api_client.get(
            "/api/health",
            headers={"Origin": "http://evil.com"}
        )
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert "http://evil.com" not in allow_origin
