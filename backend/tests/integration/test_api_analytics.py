import pytest

from main import app


def _get_route(path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route
    raise AssertionError(f"Route {path} was not found")


def test_analytics_endpoints_have_no_auth_dependency():
    for path in [
        "/api/analytics/statistics",
        "/api/analytics/best-combinations",
        "/api/analytics/comparative",
        "/api/analytics/ahp",
        "/api/analytics/pareto",
        "/api/analytics/topsis",
        "/api/analytics/epsilon-constraints",
        "/api/analytics/stability",
        "/api/analytics/sensitivity",
    ]:
        route = _get_route(path)
        assert not getattr(route.dependant, "dependencies", []), f"{path} should not have auth dependency"


def test_synthesize_endpoint_has_auth_dependency():
    route = _get_route("/api/combinations/synthesize")
    assert getattr(route.dependant, "dependencies", []), "Synthesis endpoint should remain protected"


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


@pytest.mark.integration
class TestAnalyticsAPIAccess:
    """Тесты доступности аналитических эндпоинтов без авторизации."""

    def test_statistics_without_auth(self, api_client):
        response = api_client.get("/api/analytics/statistics")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_best_combinations_without_auth(self, api_client):
        response = api_client.get("/api/analytics/best-combinations?limit=5")
        assert response.status_code == 200

    def test_comparative_without_auth(self, api_client):
        response = api_client.get("/api/analytics/comparative")
        assert response.status_code == 200

    def test_ahp_without_auth(self, api_client):
        response = api_client.post(
            "/api/analytics/ahp",
            json={"matrix": [[1, 2], [0.5, 1]]},
        )
        assert response.status_code == 200

    def test_pareto_without_auth(self, api_client):
        response = api_client.get("/api/analytics/pareto?criteria=LoD,ST&limit=6")
        assert response.status_code == 200

    def test_topsis_without_auth(self, api_client):
        response = api_client.get("/api/analytics/topsis?limit=6")
        assert response.status_code == 200

    def test_epsilon_constraints_without_auth(self, api_client):
        response = api_client.post(
            "/api/analytics/epsilon-constraints",
            json={"objective": "SN_total", "constraints": {}, "limit": 6},
        )
        assert response.status_code == 200

    def test_stability_without_auth(self, api_client):
        response = api_client.get("/api/analytics/stability?top_k=10&n_simulations=100")
        assert response.status_code == 200

    def test_sensitivity_without_auth(self, api_client):
        response = api_client.get("/api/analytics/sensitivity")
        assert response.status_code == 200

    def test_synthesize_still_requires_auth(self, api_client):
        response = api_client.post("/api/combinations/synthesize")

        import settings

        if settings.AUTH_MODE == "jwt":
            assert response.status_code == 401
        else:
            assert response.status_code == 200
