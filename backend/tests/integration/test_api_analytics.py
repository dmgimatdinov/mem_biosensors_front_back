import pytest

@pytest.mark.integration
class TestAnalyticsAPI:

    def test_statistics_endpoint(self, db_with_full_passport):
        """GET /api/analytics/statistics возвращает статистику по 5 таблицам."""
        response = db_with_full_passport.get("/api/analytics/statistics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Analytes" in data
        assert "BioRecognitionLayers" in data
        assert "ImmobilizationLayers" in data
        assert "MemristiveLayers" in data
        assert "SensorCombinations" in data

    def test_statistics_empty_db(self, api_client):
        """Статистика для пустой БД возвращает нули."""
        response = api_client.get("/api/analytics/statistics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["Analytes"]["count"] == 0
        assert data["BioRecognitionLayers"]["count"] == 0
        assert data["ImmobilizationLayers"]["count"] == 0
        assert data["MemristiveLayers"]["count"] == 0
        assert data["SensorCombinations"]["count"] == 0

    def test_best_combinations_sorted(self, db_with_full_passport):
        """GET /api/analytics/best-combinations возвращает отсортированный список."""
        db_with_full_passport.post("/api/combinations/synthesize")

        response = db_with_full_passport.get("/api/analytics/best-combinations?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 1:
            scores = [combo["Score"] for combo in data]
            assert scores == sorted(scores, reverse=True)

    def test_best_combinations_limit(self, db_with_full_passport):
        """Параметр limit работает корректно."""
        db_with_full_passport.post("/api/combinations/synthesize")

        response = db_with_full_passport.get("/api/analytics/best-combinations?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
