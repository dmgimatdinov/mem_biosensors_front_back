"""
Тесты экстремальных входных данных.
Проверяют устойчивость к XSS, null bytes, unicode, переполнениям.
"""

import pytest

from tests.factories import make_analyte


@pytest.mark.security
class TestInputValidation:
    """Тесты устойчивости к экстремальным входным данным."""

    def test_extremely_long_string_rejected(self, api_client):
        """Очень длинная строка отклоняется."""
        data = make_analyte(ta_name="A" * 10000)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 422

    def test_xss_payload_in_name(self, api_client):
        """XSS-пейлоад в имени не должен ломать API."""
        xss_payload = "<script>alert('XSS')</script>"
        data = make_analyte(ta_name=xss_payload)

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            response_get = api_client.get("/api/analytes")
            payload_found = any(item.get("TA_Name") == xss_payload for item in response_get.json())
            assert payload_found

    def test_unicode_characters_handled(self, api_client):
        """Unicode-символы обрабатываются корректно."""
        unicode_name = "Глюкоза Test 数据"
        data = make_analyte(ta_name=unicode_name)

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            response_get = api_client.get("/api/analytes")
            payload_found = any(item.get("TA_Name") == unicode_name for item in response_get.json())
            assert payload_found

    def test_null_bytes_in_string(self, api_client):
        """Null-байты в строке отклоняются или нейтрализуются."""
        data = make_analyte(ta_name="Test\x00Name")
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [200, 400, 422]

    def test_negative_numbers_where_positive_required(self, api_client):
        """Отрицательные значения для полей, требующих положительные."""
        data_tmax = make_analyte(t_max=-100)
        response_tmax = api_client.post("/api/analytes", json=data_tmax)
        assert response_tmax.status_code == 422

        data_stability = make_analyte(stability=-1)
        response_stability = api_client.post("/api/analytes", json=data_stability)
        assert response_stability.status_code == 422

    def test_float_where_int_required(self, api_client):
        """Дробные значения для целочисленных полей."""
        data = make_analyte(t_max=50.5)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [200, 422]

    def test_very_large_numbers(self, api_client):
        """Очень большие числа отклоняются."""
        data = make_analyte(t_max=999999999)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 422

    def test_special_characters_in_id(self, api_client):
        """Специальные символы в ID отклоняются."""
        special_ids = [
            "TA@001",
            "TA#001",
            "TA$001",
            "TA%001",
            "TA&001",
            "TA*001",
            "TA(001)",
            "TA 001",
        ]

        for special_id in special_ids:
            data = make_analyte(ta_id=special_id)
            response = api_client.post("/api/analytes", json=data)
            assert response.status_code in [400, 422], f"ID '{special_id}' should be rejected"

    def test_empty_strings_rejected(self, api_client):
        """Пустые строки для обязательных полей отклоняются."""
        data = make_analyte(ta_name="")
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 422

    def test_whitespace_only_strings(self, api_client):
        """Строки из пробелов обрабатываются корректно."""
        data = make_analyte(ta_name="   ")
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [200, 400, 422]

    def test_json_bomb_rejected(self, api_client):
        """Очень большой JSON отклоняется."""
        large_data = make_analyte()
        large_data["ta_name"] = "A" * 100000

        response = api_client.post("/api/analytes", json=large_data)
        assert response.status_code in [400, 413, 422]

    def test_malformed_json_rejected(self, api_client):
        """Невалидный JSON отклоняется."""
        response = api_client.post(
            "/api/analytes",
            content="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_wrong_content_type(self, api_client):
        """Неправильный Content-Type отклоняется."""
        response = api_client.post(
            "/api/analytes",
            content="ta_id=TA_TEST001",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code in [400, 415, 422]
