import io
import json
import zipfile

import pytest

from services.export_service import ExportService
from tests.factories import make_analyte

pytestmark = pytest.mark.unit


class TestExportTable:
    """Tests for ExportService.export_table()."""

    def test_export_csv_format(self, tmp_db):
        """Экспорт в CSV возвращает корректный формат."""
        tmp_db.insert_analyte(make_analyte())
        service = ExportService(tmp_db)
        payload, filename = service.export_table("Analytes", fmt="csv")
        assert "TA_TEST" in payload.decode("utf-8")
        assert "," in payload.decode("utf-8")
        assert filename.endswith(".csv")

    def test_export_json_format(self, tmp_db):
        """Экспорт в JSON возвращает валидный JSON."""
        tmp_db.insert_analyte(make_analyte())
        service = ExportService(tmp_db)
        payload, filename = service.export_table("Analytes", fmt="json")
        data = json.loads(payload.decode("utf-8"))
        assert isinstance(data, list)
        assert len(data) == 1
        assert filename.endswith(".json")

    def test_export_excel_format(self, tmp_db):
        """Экспорт в Excel возвращает корректный XLSX файл."""
        tmp_db.insert_analyte(make_analyte())
        service = ExportService(tmp_db)
        payload, filename = service.export_table("Analytes", fmt="excel")
        assert isinstance(payload, bytes)
        assert len(payload) > 0
        assert filename.endswith(".xlsx")

    def test_export_invalid_format(self, tmp_db):
        """Невалидный формат выбрасывает исключение."""
        service = ExportService(tmp_db)
        with pytest.raises(ValueError):
            service.export_table("Analytes", fmt="xml")

    def test_export_nonexistent_table(self, tmp_db):
        """Несуществующая таблица выбрасывает исключение."""
        service = ExportService(tmp_db)
        with pytest.raises(ValueError):
            service.export_table("UnknownTable", fmt="csv")

    def test_export_table_with_alias(self, tmp_db):
        """Table alias names are resolved correctly."""
        tmp_db.insert_analyte(make_analyte())
        service = ExportService(tmp_db)
        # "analytes" is a normalised key, not the SQL alias
        payload, filename = service.export_table("analytes", fmt="json")
        data = json.loads(payload.decode("utf-8"))
        assert isinstance(data, list)

    def test_export_empty_table_csv(self, tmp_db):
        """Exporting an empty table returns an empty CSV with headers."""
        service = ExportService(tmp_db)
        payload, filename = service.export_table("Analytes", fmt="csv")
        assert filename.endswith(".csv")
        # Empty table should still return valid CSV bytes
        assert isinstance(payload, bytes)


class TestExportAll:
    """Tests for ExportService.export_all()."""

    def test_export_all_json(self, tmp_db):
        """export_all в JSON возвращает словарь со всеми таблицами."""
        tmp_db.insert_analyte(make_analyte())
        service = ExportService(tmp_db)
        payload, filename = service.export_all(fmt="json")
        data = json.loads(payload.decode("utf-8"))
        assert isinstance(data, dict)
        assert "analytes" in data
        assert filename.endswith(".json")

    def test_export_all_csv_returns_zip(self, tmp_db):
        """export_all в CSV возвращает ZIP-архив."""
        service = ExportService(tmp_db)
        payload, filename = service.export_all(fmt="csv")
        assert filename.endswith(".zip")
        # Verify it's a valid ZIP file
        buf = io.BytesIO(payload)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
        assert len(names) > 0

    def test_export_all_excel(self, tmp_db):
        """export_all в Excel возвращает XLSX файл."""
        service = ExportService(tmp_db)
        payload, filename = service.export_all(fmt="excel")
        assert isinstance(payload, bytes)
        assert len(payload) > 0
        assert filename.endswith(".xlsx")

    def test_export_all_invalid_format_raises(self, tmp_db):
        """Невалидный формат в export_all выбрасывает исключение."""
        service = ExportService(tmp_db)
        with pytest.raises(ValueError):
            service.export_all(fmt="pdf")
