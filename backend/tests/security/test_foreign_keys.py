"""
Тесты целостности данных и внешних ключей.
Проверяют, что ссылочная целостность не нарушается.
"""

import pytest

from tests.factories import make_analyte, make_compatible_four_layers


@pytest.mark.security
class TestForeignKeys:
    """Тесты ссылочной целостности."""

    def test_combination_with_nonexistent_analyte_fails(self, api_client):
        """Нельзя создать комбинацию без аналита."""
        _, bio, im, mem = make_compatible_four_layers()

        api_client.post("/api/bio-recognition", json=bio)
        api_client.post("/api/immobilization", json=im)
        api_client.post("/api/memristive", json=mem)

        response = api_client.post("/api/combinations/synthesize")
        assert response.status_code == 200
        assert response.json().get("created") == 0

    def test_combination_with_nonexistent_bio_fails(self, api_client):
        """Нельзя создать комбинацию без bio слоя."""
        analyte, _, im, mem = make_compatible_four_layers()

        api_client.post("/api/analytes", json=analyte)
        api_client.post("/api/immobilization", json=im)
        api_client.post("/api/memristive", json=mem)

        response = api_client.post("/api/combinations/synthesize")
        assert response.status_code == 200
        assert response.json().get("created") == 0

    def test_combination_with_nonexistent_im_fails(self, api_client):
        """Нельзя создать комбинацию без immobilization слоя."""
        analyte, bio, _, mem = make_compatible_four_layers()

        api_client.post("/api/analytes", json=analyte)
        api_client.post("/api/bio-recognition", json=bio)
        api_client.post("/api/memristive", json=mem)

        response = api_client.post("/api/combinations/synthesize")
        assert response.status_code == 200
        assert response.json().get("created") == 0

    def test_combination_with_nonexistent_mem_fails(self, api_client):
        """Нельзя создать комбинацию без memristive слоя."""
        analyte, bio, im, _ = make_compatible_four_layers()

        api_client.post("/api/analytes", json=analyte)
        api_client.post("/api/bio-recognition", json=bio)
        api_client.post("/api/immobilization", json=im)

        response = api_client.post("/api/combinations/synthesize")
        assert response.status_code == 200
        assert response.json().get("created") == 0

    def test_cannot_create_duplicate_combination(self, api_client):
        """Нельзя создать дубликат комбинации."""
        analyte, bio, im, mem = make_compatible_four_layers()

        api_client.post("/api/analytes", json=analyte)
        api_client.post("/api/bio-recognition", json=bio)
        api_client.post("/api/immobilization", json=im)
        api_client.post("/api/memristive", json=mem)

        response_first = api_client.post("/api/combinations/synthesize")
        created_first = response_first.json().get("created", 0)
        assert created_first >= 1

        response_second = api_client.post("/api/combinations/synthesize")
        created_second = response_second.json().get("created", 0)
        assert created_second == 0

    def test_data_integrity_after_multiple_operations(self, api_client):
        """Целостность данных сохраняется после операций вставки/дубликатов."""
        for i in range(10):
            data = make_analyte(ta_id=f"TA_TEST{i:03d}")
            api_client.post("/api/analytes", json=data)

        response_initial = api_client.get("/api/analytes")
        assert response_initial.status_code == 200
        assert len(response_initial.json()) == 10

        for i in range(10):
            data = make_analyte(ta_id=f"TA_TEST{i:03d}")
            api_client.post("/api/analytes", json=data)

        response_after = api_client.get("/api/analytes")
        assert response_after.status_code == 200
        assert len(response_after.json()) == 10
