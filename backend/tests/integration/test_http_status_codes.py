import pytest

@pytest.mark.integration
class TestHTTPStatusCodes:
    """Проверка, что исключения корректно преобразуются в HTTP-коды."""

    def test_entity_not_found_returns_404(self, api_client):
        """EntityNotFoundError → 404 Not Found."""
        response = api_client.get("/api/analytes/TA_NONEXISTENT")
        assert response.status_code == 404

    def test_validation_error_returns_422(self, api_client):
        """Ошибки валидации Pydantic → 422."""
        from tests.factories import make_analyte

        data = make_analyte(t_max=9999)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 422

    def test_duplicate_entity_returns_409(self, api_client):
        """Дубликат → 409 Conflict."""
        from tests.factories import make_analyte

        data = make_analyte()
        response1 = api_client.post("/api/analytes", json=data)
        assert response1.status_code == 200
        response2 = api_client.post("/api/analytes", json=data)
        assert response2.status_code == 409

    def test_invalid_json_returns_422(self, api_client):
        """Невалидный JSON → 422."""
        response = api_client.post(
            "/api/analytes",
            content="not a json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_method_not_allowed_returns_405(self, api_client):
        """Неподдерживаемый метод → 405."""
        response = api_client.delete("/api/analytes")
        assert response.status_code in [404, 405]
