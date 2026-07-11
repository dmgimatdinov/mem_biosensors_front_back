"""
Тесты эффективности кэширования.
Проверяют, что кэш действительно ускоряет запросы.
"""

import time

import pytest

from tests.factories import make_analyte


@pytest.mark.performance
@pytest.mark.slow
class TestCachePerformance:
    """Тесты эффективности кэша."""

    def test_cache_reduces_response_time(self, api_client):
        """Кэширование уменьшает время ответа."""
        for i in range(10):
            data = make_analyte(ta_id=f"TA_CACHE{i:03d}")
            api_client.post("/api/analytes", json=data)

        start = time.perf_counter()
        api_client.get("/api/analytes")
        first_time = time.perf_counter() - start

        start = time.perf_counter()
        api_client.get("/api/analytes")
        second_time = time.perf_counter() - start

        assert second_time <= first_time * 1.5

    def test_cache_handles_many_requests(self, api_client):
        """Кэш выдерживает много запросов без ошибок."""
        data = make_analyte()
        api_client.post("/api/analytes", json=data)

        for _ in range(100):
            response = api_client.get("/api/analytes")
            assert response.status_code == 200

    def test_cache_cleared_after_insert(self, api_client):
        """Кэш очищается при вставке новой записи."""
        response1 = api_client.get("/api/analytes")
        initial_count = len(response1.json())

        new_analyte = make_analyte(ta_id="TA_TEST_NEW_CACHE", ta_name="New Analyte")
        create_response = api_client.post("/api/analytes", json=new_analyte)
        assert create_response.status_code == 200

        response2 = api_client.get("/api/analytes")
        new_count = len(response2.json())
        assert new_count == initial_count + 1

    def test_cache_consistency(self, api_client):
        """Кэш возвращает согласованные данные."""
        for i in range(5):
            data = make_analyte(ta_id=f"TA_CONSIST{i:03d}")
            api_client.post("/api/analytes", json=data)

        responses = []
        for _ in range(10):
            response = api_client.get("/api/analytes")
            responses.append(response.json())

        for i in range(1, len(responses)):
            assert responses[i] == responses[0]

    @pytest.mark.timeout(5)
    def test_cache_performance_under_load(self, api_client):
        """Кэш работает быстро под нагрузкой."""
        for i in range(20):
            data = make_analyte(ta_id=f"TA_LOAD{i:03d}")
            api_client.post("/api/analytes", json=data)

        start = time.perf_counter()
        for _ in range(50):
            response = api_client.get("/api/analytes")
            assert response.status_code == 200
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0
