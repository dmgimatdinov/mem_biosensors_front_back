import pytest


@pytest.mark.integration
class TestCRUDOperations:
    """Универсальные CRUD-тесты для всех сущностей через параметризацию."""

    def test_list_empty_returns_200(self, api_client, entity_endpoint):
        """GET на пустой БД возвращает 200 и пустой список."""
        response = api_client.get(entity_endpoint)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_valid_entity_returns_200(self, api_client, entity_endpoint, entity_factory):
        """POST с валидными данными возвращает 200."""
        data = entity_factory()
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("success") is True

    @pytest.mark.parametrize(
        "invalid_id, bad_value",
        [
            ("analyte", "INVALID_ID"),
            ("bio_recognition", "INVALID_ID"),
            ("immobilization", "INVALID_ID"),
            ("memristive", "INVALID_ID"),
        ],
    )
    def test_create_invalid_id_format_returns_422(self, api_client, entity_endpoint, entity_type, invalid_id, bad_value):
        """POST с невалидным ID возвращает 422."""
        if entity_type != invalid_id:
            pytest.skip("Не тот тип сущности")

        from tests.factories import (
            make_analyte,
            make_bio_recognition_layer,
            make_immobilization_layer,
            make_memristive_layer,
        )

        factories = {
            "analyte": (make_analyte, "ta_id"),
            "bio_recognition": (make_bio_recognition_layer, "bre_id"),
            "immobilization": (make_immobilization_layer, "im_id"),
            "memristive": (make_memristive_layer, "mem_id"),
        }
        factory, id_field = factories[entity_type]
        data = factory(**{id_field: bad_value})
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 422

    def test_create_missing_required_field_returns_422(self, api_client, entity_endpoint, entity_type):
        """POST без обязательного поля возвращает 422."""
        from tests.factories import (
            make_analyte,
            make_bio_recognition_layer,
            make_immobilization_layer,
            make_memristive_layer,
        )

        factories = {
            "analyte": (make_analyte, "ta_id"),
            "bio_recognition": (make_bio_recognition_layer, "bre_id"),
            "immobilization": (make_immobilization_layer, "im_id"),
            "memristive": (make_memristive_layer, "mem_id"),
        }
        factory, id_field = factories[entity_type]
        data = factory()
        data.pop(id_field, None)
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 422

    def test_create_out_of_range_value_returns_422(self, api_client, entity_endpoint, entity_type):
        """POST с значением вне диапазона возвращает 422."""
        from tests.factories import (
            make_analyte,
            make_bio_recognition_layer,
            make_immobilization_layer,
            make_memristive_layer,
        )

        factories = {
            "analyte": (make_analyte, {"ph_min": 999.0}),
            "bio_recognition": (make_bio_recognition_layer, {"ph_min": 999.0}),
            "immobilization": (make_immobilization_layer, {"ph_min": 999.0}),
            "memristive": (make_memristive_layer, {"ph_min": 999.0}),
        }
        factory, overrides = factories[entity_type]
        data = factory(**overrides)
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 422

    def test_create_duplicate_returns_409(self, api_client, entity_endpoint, entity_factory):
        """Повторная запись с тем же ID возвращает 409."""
        data = entity_factory()
        response1 = api_client.post(entity_endpoint, json=data)
        assert response1.status_code == 200

        response2 = api_client.post(entity_endpoint, json=data)
        assert response2.status_code == 409

    def test_list_after_create_returns_data(self, api_client, entity_endpoint, entity_factory):
        """После создания GET возвращает данные."""
        data = entity_factory()
        post_response = api_client.post(entity_endpoint, json=data)
        assert post_response.status_code == 200

        response = api_client.get(entity_endpoint)
        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 1

    def test_get_by_id_returns_200(self, api_client, entity_endpoint, entity_type, entity_factory):
        """GET /{id} возвращает 200 для существующей записи."""
        from tests.factories import (
            make_analyte,
            make_bio_recognition_layer,
            make_immobilization_layer,
            make_memristive_layer,
        )

        factories = {
            "analyte": (make_analyte, "ta_id", "TA"),
            "bio_recognition": (make_bio_recognition_layer, "bre_id", "BRE"),
            "immobilization": (make_immobilization_layer, "im_id", "IM"),
            "memristive": (make_memristive_layer, "mem_id", "MEM"),
        }
        factory, id_field, prefix = factories[entity_type]
        data = factory()
        post_response = api_client.post(entity_endpoint, json=data)
        assert post_response.status_code == 200

        entity_id = data[id_field]
        response = api_client.get(f"{entity_endpoint}/{entity_id}")
        assert response.status_code == 200
        assert response.json()[id_field.upper() if entity_type == 'analyte' else id_field.upper()] is not None

    def test_get_nonexistent_id_returns_404(self, api_client, entity_endpoint):
        """GET /{id} для несуществующей записи возвращает 404."""
        response = api_client.get(f"{entity_endpoint}/NONEXISTENT_ID_12345")
        assert response.status_code == 404

    def test_pagination_works(self, api_client, entity_endpoint, entity_factory):
        """Пагинация работает корректно."""
        for i in range(15):
            data = entity_factory()
            id_field = [k for k in data.keys() if k.endswith("_id")][0]
            data[id_field] = f"{data[id_field]}_{i:03d}"
            response = api_client.post(entity_endpoint, json=data)
            assert response.status_code == 200

        response = api_client.get(f"{entity_endpoint}?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        response = api_client.get(f"{entity_endpoint}?limit=5&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
