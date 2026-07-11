import pytest
from tests.factories import make_analyte


@pytest.mark.integration
class TestAnalytesAPISpecific:
    """Специфичные тесты для эндпоинта /api/analytes."""

    def test_create_analyte_with_unicode_name(self, api_client):
        """Аналит с unicode-именем создаётся успешно."""
        data = make_analyte(ta_name="Глюкоза 🧪 Test")
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200

        response = api_client.get("/api/analytes")
        assert response.status_code == 200
        result = response.json()
        assert any("Глюкоза" in item.get("TA_Name", "") for item in result)

    def test_create_analyte_with_boundary_ph(self, api_client):
        """Аналит с граничными значениями pH создаётся."""
        data = make_analyte(ph_min=2.0, ph_max=10.0)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200

    def test_create_analyte_with_boundary_temperature(self, api_client):
        """Аналит с граничной температурой создаётся."""
        data = make_analyte(t_max=0)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200

        data = make_analyte(ta_id="TA_TEST002", t_max=180)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200

    def test_search_by_name(self, api_client):
        """Поиск по имени работает корректно."""
        api_client.post("/api/analytes", json=make_analyte(ta_id="TA_TEST001", ta_name="Glucose"))
        api_client.post("/api/analytes", json=make_analyte(ta_id="TA_TEST002", ta_name="Fructose"))
        api_client.post("/api/analytes", json=make_analyte(ta_id="TA_TEST003", ta_name="Sucrose"))

        response = api_client.get("/api/analytes?search=Glucose")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
