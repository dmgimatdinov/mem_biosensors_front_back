import json

import pytest

from services.export_service import ExportService
from tests.factories import make_analyte

pytestmark = pytest.mark.unit


class TestExportService:
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
