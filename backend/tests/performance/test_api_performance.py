"""
Тесты производительности API.
Проверяют время ответа эндпоинтов.
"""

import time

import pytest

from tests.factories import make_analyte


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """Тесты производительности API."""

    @pytest.mark.timeout(2)
    def test_health_endpoint_performance(self, api_client):
        """GET /api/health выполняется быстро."""
        start = time.perf_counter()
        response = api_client.get("/api/health")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert elapsed < 2.0

    @pytest.mark.timeout(5)
    def test_list_empty_endpoint_performance(self, api_client):
        """GET /api/analytes на пустой БД выполняется быстро."""
        start = time.perf_counter()
        response = api_client.get("/api/analytes")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert elapsed < 5.0

    @pytest.mark.timeout(10)
    def test_list_large_dataset_performance(self, api_client):
        """GET /api/analytes с 100 записями выполняется быстро."""
        for i in range(100):
            data = make_analyte(ta_id=f"TA_PERF{i:03d}")
            api_client.post("/api/analytes", json=data)

        start = time.perf_counter()
        response = api_client.get("/api/analytes?limit=200")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert len(response.json()) == 100
        assert elapsed < 10.0

    @pytest.mark.timeout(5)
    def test_create_endpoint_performance(self, api_client):
        """POST /api/analytes выполняется быстро."""
        data = make_analyte()

        start = time.perf_counter()
        response = api_client.post("/api/analytes", json=data)
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert elapsed < 5.0

    @pytest.mark.timeout(5)
    def test_get_by_id_performance(self, api_client):
        """GET /api/analytes/{id} выполняется быстро."""
        data = make_analyte()
        api_client.post("/api/analytes", json=data)

        start = time.perf_counter()
        response = api_client.get(f"/api/analytes/{data['ta_id']}")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert elapsed < 5.0

    @pytest.mark.timeout(10)
    def test_pagination_performance(self, api_client):
        """Пагинация работает быстро."""
        for i in range(200):
            data = make_analyte(ta_id=f"TA_PAGE{i:03d}")
            api_client.post("/api/analytes", json=data)

        start = time.perf_counter()
        response = api_client.get("/api/analytes?limit=50&offset=100")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert len(response.json()) == 50
        assert elapsed < 10.0
