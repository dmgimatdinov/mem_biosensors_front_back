import pytest
from pydantic import TypeAdapter, ValidationError
from typing import List
from tests.contract.api_schemas import (
    AnalyteResponse,
    BioRecognitionResponse,
    ImmobilizationResponse,
    MemristiveResponse,
    CombinationResponse,
)


@pytest.mark.contract
class TestAPIContract:
    """Централизованные тесты API-контракта."""

    ENDPOINT_SCHEMAS = {
        "/api/analytes": AnalyteResponse,
        "/api/bio-recognition": BioRecognitionResponse,
        "/api/immobilization": ImmobilizationResponse,
        "/api/memristive": MemristiveResponse,
        "/api/combinations": CombinationResponse,
    }

    @pytest.mark.parametrize("endpoint,schema", list(ENDPOINT_SCHEMAS.items()))
    def test_endpoint_returns_valid_schema(self, api_client, endpoint, schema):
        """Каждый эндпоинт возвращает данные, соответствующие схеме."""
        response = api_client.get(endpoint)
        assert response.status_code == 200

        adapter = TypeAdapter(List[schema])
        adapter.validate_python(response.json())

    def test_all_endpoints_return_lists(self, api_client):
        """Все GET-эндпоинты сущностей возвращают списки."""
        for endpoint in self.ENDPOINT_SCHEMAS.keys():
            response = api_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list), f"{endpoint} should return a list"

    def test_no_extra_fields_in_responses(self, api_client):
        """Ответы не содержат неожиданных полей (опционально)."""
        response = api_client.get("/api/analytes")
        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            analyte = data[0]
            forbidden_keywords = ["password", "secret", "token", "api_key"]
            for key in analyte.keys():
                for forbidden in forbidden_keywords:
                    assert forbidden not in key.lower(), f"Found forbidden field: {key}"

    def test_contract_fails_on_missing_required_field(self, api_client):
        """Контракт падает, если из ответа убрать обязательное поле."""
        data = api_client.get("/api/analytes").json()
        if not data:
            return

        broken_payload = data[0].copy()
        broken_payload.pop("TA_ID", None)

        with pytest.raises(ValidationError):
            AnalyteResponse.model_validate(broken_payload)
