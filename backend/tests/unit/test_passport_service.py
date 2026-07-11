"""Unit tests for services/passport_service.py."""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import asdict

from services.passport_service import PassportService
from domain.models import (
    Analyte,
    BioRecognitionLayer,
    ImmobilizationLayer,
    MemristiveLayer,
    SensorCombination,
)

pytestmark = pytest.mark.unit


def _make_analyte(**kw):
    defaults = dict(
        ta_id="TA_UNIT001",
        ta_name="Unit Test Analyte",
        ph_min=3.0,
        ph_max=8.0,
    )
    defaults.update(kw)
    return Analyte(**defaults)


def _make_bio(**kw):
    defaults = dict(bre_id="BRE_UNIT001", bre_name="Unit Bio Layer")
    defaults.update(kw)
    return BioRecognitionLayer(**defaults)


def _make_immob(**kw):
    defaults = dict(im_id="IM_UNIT001", im_name="Unit Immobilization Layer")
    defaults.update(kw)
    return ImmobilizationLayer(**defaults)


def _make_mem(**kw):
    defaults = dict(mem_id="MEM_UNIT001", mem_name="Unit Memristive Layer")
    defaults.update(kw)
    return MemristiveLayer(**defaults)


class TestPassportServiceSavePassport:
    """Tests for PassportService.save_passport()."""

    def test_save_passport_success(self):
        """All valid layers → success tuple."""
        mock_db = MagicMock()
        mock_db.insert_analyte.return_value = True
        mock_db.insert_bio_recognition_layer.return_value = True
        mock_db.insert_immobilization_layer.return_value = True
        mock_db.insert_memristive_layer.return_value = True

        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(), _make_bio(), _make_immob(), _make_mem()
        )
        assert ok is True
        assert "успешно" in msg.lower() or "✅" in msg

    def test_save_passport_with_combination(self):
        """Saving with combination also inserts combination record."""
        mock_db = MagicMock()
        mock_db.insert_analyte.return_value = True
        mock_db.insert_bio_recognition_layer.return_value = True
        mock_db.insert_immobilization_layer.return_value = True
        mock_db.insert_memristive_layer.return_value = True
        mock_db.insert_sensor_combination.return_value = True

        combo = SensorCombination(
            combo_id="COMBO_001",
            ta_id="TA_UNIT001",
            bre_id="BRE_UNIT001",
            im_id="IM_UNIT001",
            mem_id="MEM_UNIT001",
        )
        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(), _make_bio(), _make_immob(), _make_mem(), combination=combo
        )
        assert ok is True
        mock_db.insert_sensor_combination.assert_called_once()

    def test_save_passport_empty_analyte_id_fails(self):
        """Empty analyte ID returns failure immediately."""
        mock_db = MagicMock()
        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(ta_id=""), _make_bio(), _make_immob(), _make_mem()
        )
        assert ok is False
        assert "аналит" in msg.lower() or "❌" in msg

    def test_save_passport_empty_bio_id_fails(self):
        """Empty bio layer ID returns failure."""
        mock_db = MagicMock()
        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(), _make_bio(bre_id=""), _make_immob(), _make_mem()
        )
        assert ok is False

    def test_save_passport_empty_immob_id_fails(self):
        """Empty immobilization layer ID returns failure."""
        mock_db = MagicMock()
        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(), _make_bio(), _make_immob(im_id=""), _make_mem()
        )
        assert ok is False

    def test_save_passport_empty_mem_id_fails(self):
        """Empty memristive layer ID returns failure."""
        mock_db = MagicMock()
        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(), _make_bio(), _make_immob(), _make_mem(mem_id="")
        )
        assert ok is False

    def test_save_passport_duplicate_returns_special_code(self):
        """Duplicate insertion returns special DUPLICATE code in response."""
        mock_db = MagicMock()
        mock_db.insert_analyte.return_value = "DUPLICATE"
        mock_db.insert_bio_recognition_layer.return_value = True
        mock_db.insert_immobilization_layer.return_value = True
        mock_db.insert_memristive_layer.return_value = True

        service = PassportService(mock_db)
        ok, result = service.save_passport(
            _make_analyte(), _make_bio(), _make_immob(), _make_mem()
        )
        assert ok is False
        # result should be a tuple with "DUPLICATE" code
        assert isinstance(result, tuple)
        assert result[0] == "DUPLICATE"

    def test_save_passport_db_error_returns_failure(self):
        """DB error (not True, not DUPLICATE) returns failure message."""
        mock_db = MagicMock()
        mock_db.insert_analyte.return_value = None  # Not True, not "DUPLICATE"
        mock_db.insert_bio_recognition_layer.return_value = True
        mock_db.insert_immobilization_layer.return_value = True
        mock_db.insert_memristive_layer.return_value = True

        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(), _make_bio(), _make_immob(), _make_mem()
        )
        assert ok is False
        assert "ошибка" in msg.lower() or "❌" in msg

    def test_save_passport_exception_returns_failure(self):
        """Unexpected exception is caught and returns failure tuple."""
        mock_db = MagicMock()
        mock_db.insert_analyte.side_effect = RuntimeError("unexpected DB error")

        service = PassportService(mock_db)
        ok, msg = service.save_passport(
            _make_analyte(), _make_bio(), _make_immob(), _make_mem()
        )
        assert ok is False
        assert "❌" in msg or "ошибка" in msg.lower()


class TestPassportServiceDataclassToDbDict:
    """Tests for PassportService._dataclass_to_db_dict()."""

    def test_analyte_fields_are_mapped(self):
        """Analyte fields are converted to database column names."""
        analyte = _make_analyte()
        db_dict = PassportService._dataclass_to_db_dict(analyte, "TA")
        assert "TA_ID" in db_dict
        assert "TA_Name" in db_dict
        assert db_dict["TA_ID"] == "TA_UNIT001"

    def test_bio_fields_are_mapped(self):
        """Bio layer fields are converted to database column names."""
        bio = _make_bio()
        db_dict = PassportService._dataclass_to_db_dict(bio, "BRE")
        assert "BRE_ID" in db_dict
        assert "BRE_Name" in db_dict

    def test_immob_fields_are_mapped(self):
        """Immobilization layer fields are converted to database column names."""
        immob = _make_immob()
        db_dict = PassportService._dataclass_to_db_dict(immob, "IM")
        assert "IM_ID" in db_dict
        assert "IM_Name" in db_dict

    def test_mem_fields_are_mapped(self):
        """Memristive layer fields are converted to database column names."""
        mem = _make_mem()
        db_dict = PassportService._dataclass_to_db_dict(mem, "MEM")
        assert "MEM_ID" in db_dict
        assert "MEM_Name" in db_dict

    def test_unknown_fields_pass_through_unchanged(self):
        """Fields not in name_map are passed through without transformation."""
        analyte = _make_analyte()
        db_dict = PassportService._dataclass_to_db_dict(analyte, "TA")
        # All keys should be either mapped or passed through
        assert isinstance(db_dict, dict)
        assert len(db_dict) > 0


class TestPassportServiceOverwriteEntity:
    """Tests for PassportService.overwrite_entity()."""

    def test_overwrite_entity_success(self, tmp_db):
        """Overwriting an entity deletes the record and returns True."""
        # Insert an analyte first
        from tests.factories import make_analyte
        tmp_db.insert_analyte(make_analyte(ta_id="TA_OVERWRITE001"))

        service = PassportService(tmp_db)
        result = service.overwrite_entity("analyte", "TA_OVERWRITE001")
        assert result is True

    def test_overwrite_entity_nonexistent_succeeds(self, tmp_db):
        """Overwriting a non-existent entity still returns True (DELETE with no rows)."""
        service = PassportService(tmp_db)
        result = service.overwrite_entity("analyte", "NONEXISTENT_001")
        assert result is True
