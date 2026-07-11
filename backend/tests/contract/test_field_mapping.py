import pytest
from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
)


@pytest.mark.contract
class TestFieldMapping:
    """Проверка, что бэкенд отдаёт поля в правильном регистре."""

    def test_analyte_fields_are_pascal_case(self, api_client):
        """Поля аналита в ответе используют PascalCase."""
        data = make_analyte()
        api_client.post("/api/analytes", json=data)

        response = api_client.get("/api/analytes")
        assert response.status_code == 200
        response_data = response.json()

        if len(response_data) > 0:
            analyte = response_data[0]
            assert "TA_ID" in analyte
            assert "TA_Name" in analyte
            assert "PH_Min" in analyte
            assert "PH_Max" in analyte
            assert "T_Max" in analyte
            assert "ta_id" not in analyte
            assert "ta_name" not in analyte
            assert "ph_min" not in analyte

    def test_immobilization_special_fields(self, api_client):
        """Специальные поля иммобилизации проверяются в GET /api/immobilization/{id}."""
        data = make_immobilization_layer()
        api_client.post("/api/immobilization", json=data)

        response = api_client.get(f"/api/immobilization/{data['im_id']}")
        assert response.status_code == 200
        im = response.json()

        assert "MP" in im
        assert "Adh" in im
        assert "Sol" in im
        assert "K_IM" in im
        assert "young_modulus" not in im
        assert "adhesion" not in im
        assert "solubility" not in im
        assert "loss_coefficient" not in im

    def test_combination_fields_are_pascal_case(self, db_with_full_passport):
        """Поля комбинации в ответе используют PascalCase."""
        db_with_full_passport.post("/api/combinations/synthesize")
        response = db_with_full_passport.get("/api/combinations")
        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            combo = data[0]
            assert "Combo_ID" in combo
            assert "TA_ID" in combo
            assert "BRE_ID" in combo
            assert "IM_ID" in combo
            assert "MEM_ID" in combo
            assert "Score" in combo
            assert "combo_id" not in combo
            assert "ta_id" not in combo

    def test_id_format_matches_contract(self, api_client):
        """ID сущностей соответствуют регулярным выражениям из контракта."""
        from tests.contract.api_schemas import AnalyteResponse
        from pydantic import TypeAdapter

        data = make_analyte()
        api_client.post("/api/analytes", json=data)

        response = api_client.get("/api/analytes")
        assert response.status_code == 200
        adapter = TypeAdapter(AnalyteResponse)

        for item in response.json():
            adapter.validate_python(item)
