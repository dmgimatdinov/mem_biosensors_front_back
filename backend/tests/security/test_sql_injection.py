"""
Тесты SQL-инъекций.
Проверяют, что параметризованные запросы нейтрализуют SQL-атаки.
"""

import pytest

from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
)


@pytest.mark.security
class TestSQLInjection:
    """Тесты устойчивости к SQL-инъекциям."""

    def test_sql_injection_in_id_field(self, api_client):
        """SQL-инъекция в ta_id не выполняется."""
        malicious_id = "TA001'; DROP TABLE Analytes; --"
        data = make_analyte(ta_id=malicious_id)

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [400, 422]

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200

    def test_sql_injection_in_name_field(self, api_client):
        """SQL-инъекция в ta_name не выполняется."""
        malicious_name = "Test'; DROP TABLE Analytes; --"
        data = make_analyte(ta_name=malicious_name)

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [200, 400, 422]

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200

    def test_sql_injection_in_numeric_field(self, api_client):
        """SQL-инъекция в числовом поле отклоняется валидацией."""
        data = make_analyte(t_max="50; DROP TABLE Analytes;")

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 422

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200

    def test_sql_injection_in_search_param(self, api_client):
        """SQL-инъекция в параметре поиска не выполняется."""
        malicious_search = "'; DROP TABLE Analytes; --"
        response = api_client.get(f"/api/analytes?search={malicious_search}")

        assert response.status_code in [200, 400, 422]

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200

    def test_sql_injection_union_attack(self, api_client):
        """UNION-based SQL-инъекция не выполняется."""
        malicious_id = "TA001' UNION SELECT * FROM Analytes --"
        data = make_analyte(ta_id=malicious_id)

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [400, 422]

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200

    def test_sql_injection_blind_attack(self, api_client):
        """Blind SQL-инъекция не выполняется."""
        malicious_id = "TA001' AND 1=1 --"
        data = make_analyte(ta_id=malicious_id)

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [400, 422]

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200

    @pytest.mark.parametrize(
        "malicious_payload",
        [
            "'; DROP TABLE Analytes; --",
            "'; DELETE FROM Analytes WHERE '1'='1",
            "'; INSERT INTO Analytes VALUES('HACKED'); --",
            "'; UPDATE Analytes SET TA_Name='HACKED'; --",
            "TA001' OR '1'='1",
            "TA001'; EXEC sp_executesql N'DROP TABLE Analytes'; --",
        ],
    )
    def test_various_sql_injection_payloads(self, api_client, malicious_payload):
        """Различные SQL-инъекции отклоняются или нейтрализуются."""
        data = make_analyte(ta_name=malicious_payload)

        response = api_client.post("/api/analytes", json=data)
        assert response.status_code in [200, 400, 422]

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200

    def test_sql_injection_in_all_entities(self, api_client):
        """SQL-инъекции отклоняются/нейтрализуются во всех сущностях."""
        malicious = "'; DROP TABLE Analytes; --"

        bio = make_bio_recognition_layer(bre_name=malicious)
        response_bio = api_client.post("/api/bio-recognition", json=bio)
        assert response_bio.status_code in [200, 400, 422]

        im = make_immobilization_layer(im_name=malicious)
        response_im = api_client.post("/api/immobilization", json=im)
        assert response_im.status_code in [200, 400, 422]

        mem = make_memristive_layer(mem_name=malicious)
        response_mem = api_client.post("/api/memristive", json=mem)
        assert response_mem.status_code in [200, 400, 422]

        response_check = api_client.get("/api/analytes")
        assert response_check.status_code == 200
