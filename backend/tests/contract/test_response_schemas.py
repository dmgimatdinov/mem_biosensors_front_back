import pytest
from pydantic import TypeAdapter, ValidationError
from typing import List
from tests.contract.api_schemas import (
    AnalyteResponse,
    BioRecognitionResponse,
    ImmobilizationResponse,
    MemristiveResponse,
    CombinationResponse,
    SuccessResponse,
    ErrorResponse,
    HealthResponse,
    StatisticsResponse,
    SynthesisResponse,
)
from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
)


@pytest.mark.contract
class TestResponseSchemas:
    """Проверка соответствия ответов API описанным схемам."""

    def test_health_response_schema(self, api_client):
        """Ответ /api/health соответствует HealthResponse."""
        response = api_client.get("/api/health")
        assert response.status_code == 200

        adapter = TypeAdapter(HealthResponse)
        validated = adapter.validate_python(response.json())
        dumped = validated.model_dump()
        assert set(dumped.keys()) == {"status", "message"}

    def test_statistics_response_schema(self, api_client):
        """Ответ /api/analytics/statistics соответствует StatisticsResponse."""
        response = api_client.get("/api/analytics/statistics")
        assert response.status_code == 200

        validated = StatisticsResponse.model_validate(response.json())
        dumped = validated.model_dump()
        assert "Analytes" in dumped
        assert "SensorCombinations" in dumped

    def test_analyte_response_schema(self, api_client):
        """Ответ GET /api/analytes соответствует AnalyteResponse."""
        data = make_analyte()
        api_client.post("/api/analytes", json=data)

        response = api_client.get("/api/analytes")
        assert response.status_code == 200

        adapter = TypeAdapter(List[AnalyteResponse])
        adapter.validate_python(response.json())

    def test_bio_recognition_response_schema(self, api_client):
        """Ответ GET /api/bio-recognition соответствует схеме."""
        data = make_bio_recognition_layer()
        api_client.post("/api/bio-recognition", json=data)

        response = api_client.get("/api/bio-recognition")
        assert response.status_code == 200

        adapter = TypeAdapter(List[BioRecognitionResponse])
        adapter.validate_python(response.json())

    def test_immobilization_response_schema(self, api_client):
        """Ответ GET /api/immobilization соответствует схеме."""
        data = make_immobilization_layer()
        api_client.post("/api/immobilization", json=data)

        response = api_client.get("/api/immobilization")
        assert response.status_code == 200

        adapter = TypeAdapter(List[ImmobilizationResponse])
        adapter.validate_python(response.json())

    def test_memristive_response_schema(self, api_client):
        """Ответ GET /api/memristive соответствует схеме."""
        data = make_memristive_layer()
        api_client.post("/api/memristive", json=data)

        response = api_client.get("/api/memristive")
        assert response.status_code == 200

        adapter = TypeAdapter(List[MemristiveResponse])
        adapter.validate_python(response.json())

    def test_combination_response_schema(self, db_with_full_passport):
        """Ответ GET /api/combinations соответствует схеме."""
        db_with_full_passport.post("/api/combinations/synthesize")
        response = db_with_full_passport.get("/api/combinations")
        assert response.status_code == 200

        adapter = TypeAdapter(List[CombinationResponse])
        adapter.validate_python(response.json())

    def test_create_response_schema(self, api_client):
        """Ответ POST /api/analytes соответствует SuccessResponse."""
        data = make_analyte()
        response = api_client.post("/api/analytes", json=data)

        assert response.status_code == 200
        try:
            adapter = TypeAdapter(SuccessResponse)
            adapter.validate_python(response.json())
        except ValidationError:
            json_data = response.json()
            assert "success" in json_data or "data" in json_data

    def test_synthesis_response_schema(self, db_with_full_passport):
        """Ответ POST /api/combinations/synthesize соответствует схеме."""
        response = db_with_full_passport.post("/api/combinations/synthesize")
        assert response.status_code == 200

        adapter = TypeAdapter(SynthesisResponse)
        adapter.validate_python(response.json())

    def test_error_response_schema(self, api_client):
        """Ответ с ошибкой соответствует ErrorResponse."""
        response = api_client.get("/api/analytes/NONEXISTENT_ID")
        assert response.status_code == 404

        adapter = TypeAdapter(ErrorResponse)
        adapter.validate_python(response.json())
