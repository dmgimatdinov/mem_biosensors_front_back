"""
Тесты производительности синтеза комбинаций.
Проверяют, что синтез укладывается в разумные таймауты.
"""

import pytest

from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
)


@pytest.mark.performance
@pytest.mark.slow
class TestSynthesisPerformance:
    """Тесты производительности синтеза."""

    @pytest.mark.timeout(30)
    def test_synthesize_1000_combinations_performance(self, api_client):
        """Синтез 1000 комбинаций укладывается в 30 секунд."""
        for i in range(10):
            analyte = make_analyte(ta_id=f"TA_TEST{i:03d}")
            api_client.post("/api/analytes", json=analyte)

            bio = make_bio_recognition_layer(bre_id=f"BRE_TEST{i:03d}")
            api_client.post("/api/bio-recognition", json=bio)

            im = make_immobilization_layer(im_id=f"IM_TEST{i:03d}")
            api_client.post("/api/immobilization", json=im)

            mem = make_memristive_layer(mem_id=f"MEM_TEST{i:03d}")
            api_client.post("/api/memristive", json=mem)

        response = api_client.post("/api/combinations/synthesize?max_combinations=1000")
        assert response.status_code == 200

        data = response.json()
        assert data["checked"] <= 1000

    @pytest.mark.timeout(60)
    def test_synthesize_10000_combinations_performance(self, api_client):
        """Синтез 10000 комбинаций укладывается в 60 секунд."""
        for i in range(18):
            analyte = make_analyte(ta_id=f"TA_PERF{i:03d}")
            api_client.post("/api/analytes", json=analyte)

            bio = make_bio_recognition_layer(bre_id=f"BRE_PERF{i:03d}")
            api_client.post("/api/bio-recognition", json=bio)

            im = make_immobilization_layer(im_id=f"IM_PERF{i:03d}")
            api_client.post("/api/immobilization", json=im)

            mem = make_memristive_layer(mem_id=f"MEM_PERF{i:03d}")
            api_client.post("/api/memristive", json=mem)

        response = api_client.post("/api/combinations/synthesize?max_combinations=10000")
        assert response.status_code == 200

        data = response.json()
        assert data["checked"] <= 10000

    @pytest.mark.timeout(10)
    def test_synthesize_empty_db_performance(self, api_client):
        """Синтез на пустой БД выполняется быстро."""
        response = api_client.post("/api/combinations/synthesize")
        assert response.status_code == 200

        data = response.json()
        assert data["checked"] == 0
        assert data["created"] == 0

    @pytest.mark.timeout(15)
    def test_repeated_synthesis_performance(self, api_client):
        """Повторный синтез (дубликаты) выполняется быстро."""
        for i in range(5):
            analyte = make_analyte(ta_id=f"TA_REPEAT{i:03d}")
            api_client.post("/api/analytes", json=analyte)

            bio = make_bio_recognition_layer(bre_id=f"BRE_REPEAT{i:03d}")
            api_client.post("/api/bio-recognition", json=bio)

            im = make_immobilization_layer(im_id=f"IM_REPEAT{i:03d}")
            api_client.post("/api/immobilization", json=im)

            mem = make_memristive_layer(mem_id=f"MEM_REPEAT{i:03d}")
            api_client.post("/api/memristive", json=mem)

        response1 = api_client.post("/api/combinations/synthesize")
        assert response1.status_code == 200

        response2 = api_client.post("/api/combinations/synthesize")
        assert response2.status_code == 200

        data2 = response2.json()
        assert data2["created"] == 0
