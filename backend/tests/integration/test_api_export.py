import pytest
import json
import zipfile
import io

from tests.factories import make_analyte

@pytest.mark.integration
class TestExportAPI:

    def test_export_csv(self, db_with_analytes):
        """GET /api/export/analytes?format=csv → 200, text/csv."""
        response = db_with_analytes.get("/api/export/analytes?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert len(response.content) > 0
        content = response.text
        assert "," in content or ";" in content

    def test_export_json(self, db_with_analytes):
        """GET /api/export/analytes?format=json → 200, application/json."""
        response = db_with_analytes.get("/api/export/analytes?format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        data = json.loads(response.content)
        assert isinstance(data, list)

    def test_export_excel(self, db_with_analytes):
        """GET /api/export/analytes?format=excel → 200, xlsx."""
        response = db_with_analytes.get("/api/export/analytes?format=excel")
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
        assert len(response.content) > 0

    def test_export_all_zip(self, db_with_analytes):
        """GET /api/export/all?format=csv → ZIP-архив."""
        response = db_with_analytes.get("/api/export/all?format=csv")
        assert response.status_code == 200
        assert "application/zip" in response.headers["content-type"]

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        assert len(zip_file.namelist()) > 0

    def test_export_invalid_format(self, api_client):
        """format=xml → 422."""
        response = api_client.get("/api/export/analytes?format=xml")
        assert response.status_code == 422

    def test_export_nonexistent_table(self, api_client):
        """table_name=unknown → 404."""
        response = api_client.get("/api/export/unknown_table?format=csv")
        assert response.status_code == 404

    def test_export_empty_table(self, api_client):
        """Экспорт пустой таблицы возвращает валидный файл."""
        response = api_client.get("/api/export/analytes?format=csv")
        assert response.status_code == 200
        assert len(response.content) > 0
