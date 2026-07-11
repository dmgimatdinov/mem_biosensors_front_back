import pytest

@pytest.mark.integration
class TestCacheBehavior:
    """Проверка корректности работы кэша."""

    def test_cache_cleared_after_insert(self, api_client):
        """Кэш очищается при вставке новой записи."""
        response1 = api_client.get("/api/analytes")
        assert response1.status_code == 200
        initial_count = len(response1.json())

        from tests.factories import make_analyte
        new_analyte = make_analyte(ta_id="TA_TEST_NEW", ta_name="New Analyte")
        post_response = api_client.post("/api/analytes", json=new_analyte)
        assert post_response.status_code == 200

        response2 = api_client.get("/api/analytes")
        assert response2.status_code == 200
        new_count = len(response2.json())
        assert new_count == initial_count + 1

    def test_cache_cleared_after_delete(self, api_client):
        """Кэш очищается при удалении записи."""
        pytest.skip("DELETE endpoint not implemented")

    def test_repeated_reads_consistent(self, api_client):
        """Повторные чтения возвращают одинаковые данные."""
        from tests.factories import make_analyte

        data = make_analyte()
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200

        response1 = api_client.get("/api/analytes")
        response2 = api_client.get("/api/analytes")

        assert response1.json() == response2.json()
