"""Unit tests for services/biosensor_service.py.

Tests cover ValidationResult, ConstraintValidator, UniversalBiosensorValidator,
UniversalCRUDManager, and BiosensorService.
"""

import pytest
from unittest.mock import MagicMock

from services.biosensor_service import (
    ValidationResult,
    ConstraintValidator,
    UniversalBiosensorValidator,
    UniversalCRUDManager,
    BiosensorService,
    SENSOR_LAYERS_CONFIG,
)
from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
)

pytestmark = pytest.mark.unit


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_initial_valid_state(self):
        """New ValidationResult starts as valid with empty errors/warnings."""
        result = ValidationResult(is_valid=True, entity_type="analyte", entity_id="TA001")
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
        assert result.entity_type == "analyte"
        assert result.entity_id == "TA001"

    def test_initial_invalid_state(self):
        """ValidationResult can start as invalid."""
        result = ValidationResult(is_valid=False, entity_type="analyte", entity_id=None)
        assert not result.is_valid

    def test_add_error_marks_invalid(self):
        """Adding an error sets is_valid to False."""
        result = ValidationResult(is_valid=True, entity_type="analyte", entity_id="TA001")
        result.add_error("Something is wrong")
        assert not result.is_valid
        assert "Something is wrong" in result.errors

    def test_add_multiple_errors(self):
        """Multiple errors are accumulated."""
        result = ValidationResult(is_valid=True, entity_type="analyte", entity_id="TA001")
        result.add_error("Error 1")
        result.add_error("Error 2")
        assert len(result.errors) == 2

    def test_add_warning_does_not_affect_validity(self):
        """Adding a warning does not change is_valid."""
        result = ValidationResult(is_valid=True, entity_type="analyte", entity_id="TA001")
        result.add_warning("A warning")
        assert result.is_valid
        assert "A warning" in result.warnings

    def test_bool_true_when_valid(self):
        """bool(result) is True when valid."""
        result = ValidationResult(is_valid=True, entity_type="analyte", entity_id="TA001")
        assert bool(result) is True

    def test_bool_false_when_invalid(self):
        """bool(result) is False when invalid."""
        result = ValidationResult(is_valid=False, entity_type="analyte", entity_id="TA001")
        assert bool(result) is False

    def test_post_init_with_explicit_errors(self):
        """ValidationResult accepts explicit errors list."""
        result = ValidationResult(
            is_valid=False,
            entity_type="analyte",
            entity_id="TA001",
            errors=["Existing error"],
        )
        assert result.errors == ["Existing error"]


class TestConstraintValidator:
    """Tests for ConstraintValidator static methods."""

    # --- validate_type ---
    def test_validate_type_correct_type(self):
        """Returns None when value matches expected type."""
        assert ConstraintValidator.validate_type("hello", str) is None
        assert ConstraintValidator.validate_type(42, int) is None
        assert ConstraintValidator.validate_type(3.14, float) is None

    def test_validate_type_wrong_type(self):
        """Returns error message when value has wrong type."""
        error = ConstraintValidator.validate_type(123, str)
        assert error is not None
        assert "str" in error or "int" in error

    def test_validate_type_none_value(self):
        """Returns None for None value (None is allowed)."""
        assert ConstraintValidator.validate_type(None, str) is None

    # --- validate_range ---
    def test_validate_range_within_bounds(self):
        """Returns None when value is within range."""
        assert ConstraintValidator.validate_range(5.0, {"min": 0.0, "max": 10.0}) is None

    def test_validate_range_at_min_boundary(self):
        """Returns None when value equals minimum."""
        assert ConstraintValidator.validate_range(0.0, {"min": 0.0, "max": 10.0}) is None

    def test_validate_range_at_max_boundary(self):
        """Returns None when value equals maximum."""
        assert ConstraintValidator.validate_range(10.0, {"min": 0.0, "max": 10.0}) is None

    def test_validate_range_below_min(self):
        """Returns error when value is below minimum."""
        error = ConstraintValidator.validate_range(-1.0, {"min": 0.0, "max": 10.0})
        assert error is not None
        assert "мин" in error.lower() or "min" in error.lower()

    def test_validate_range_above_max(self):
        """Returns error when value is above maximum."""
        error = ConstraintValidator.validate_range(11.0, {"min": 0.0, "max": 10.0})
        assert error is not None
        assert "макс" in error.lower() or "max" in error.lower()

    def test_validate_range_only_min(self):
        """Works with only min constraint."""
        assert ConstraintValidator.validate_range(5.0, {"min": 0.0}) is None
        assert ConstraintValidator.validate_range(-1.0, {"min": 0.0}) is not None

    def test_validate_range_only_max(self):
        """Works with only max constraint."""
        assert ConstraintValidator.validate_range(5.0, {"max": 10.0}) is None
        assert ConstraintValidator.validate_range(11.0, {"max": 10.0}) is not None

    # --- validate_length ---
    def test_validate_length_within_bounds(self):
        """Returns None when string length is within bounds."""
        assert ConstraintValidator.validate_length("hello", {"min_length": 3, "max_length": 10}) is None

    def test_validate_length_too_short(self):
        """Returns error when string is too short."""
        error = ConstraintValidator.validate_length("ab", {"min_length": 3})
        assert error is not None

    def test_validate_length_too_long(self):
        """Returns error when string is too long."""
        error = ConstraintValidator.validate_length("a" * 20, {"max_length": 10})
        assert error is not None

    def test_validate_length_exact_min(self):
        """Returns None when string length equals minimum."""
        assert ConstraintValidator.validate_length("abc", {"min_length": 3}) is None

    def test_validate_length_exact_max(self):
        """Returns None when string length equals maximum."""
        assert ConstraintValidator.validate_length("abcde", {"max_length": 5}) is None

    # --- validate_enum ---
    def test_validate_enum_valid_value(self):
        """Returns None when value is in allowed list."""
        assert ConstraintValidator.validate_enum("low", {"enum": ["low", "medium", "high"]}) is None

    def test_validate_enum_invalid_value(self):
        """Returns error when value is not in allowed list."""
        error = ConstraintValidator.validate_enum("extreme", {"enum": ["low", "medium", "high"]})
        assert error is not None

    # --- validate_pattern ---
    def test_validate_pattern_matching(self):
        """Returns None when value matches the pattern."""
        assert ConstraintValidator.validate_pattern("TA001", {"pattern": r"^TA[A-Z0-9_-]{1,20}$"}) is None

    def test_validate_pattern_not_matching(self):
        """Returns error when value does not match the pattern."""
        error = ConstraintValidator.validate_pattern("ABC001", {"pattern": r"^TA[A-Z0-9_-]{1,20}$"})
        assert error is not None

    def test_validate_pattern_missing_pattern_key(self):
        """Returns None when no pattern key in constraint."""
        assert ConstraintValidator.validate_pattern("anything", {}) is None


class TestUniversalBiosensorValidator:
    """Tests for UniversalBiosensorValidator."""

    def test_valid_analyte_passes(self):
        """Valid analyte data passes validation."""
        validator = UniversalBiosensorValidator()
        result = validator.validate("analyte", make_analyte())
        assert result.is_valid

    def test_valid_bio_recognition_passes(self):
        """Valid bio-recognition layer data passes validation."""
        validator = UniversalBiosensorValidator()
        result = validator.validate("bio_recognition", make_bio_recognition_layer())
        assert result.is_valid

    def test_valid_immobilization_passes(self):
        """Valid immobilization layer data passes validation."""
        validator = UniversalBiosensorValidator()
        result = validator.validate("immobilization", make_immobilization_layer())
        assert result.is_valid

    def test_valid_memristive_passes(self):
        """Valid memristive layer data passes validation."""
        validator = UniversalBiosensorValidator()
        result = validator.validate("memristive", make_memristive_layer())
        assert result.is_valid

    def test_unknown_entity_type_fails(self):
        """Unknown entity type returns failure result."""
        validator = UniversalBiosensorValidator()
        result = validator.validate("unknown_type", {})
        assert not result.is_valid
        assert any("Неизвестный тип" in err for err in result.errors)

    def test_missing_required_field_fails(self):
        """Missing required field causes validation failure."""
        validator = UniversalBiosensorValidator()
        data = {"ta_name": "Test Analyte"}  # missing ta_id
        result = validator.validate("analyte", data)
        assert not result.is_valid

    def test_wrong_type_fails(self):
        """Wrong field type causes validation failure."""
        validator = UniversalBiosensorValidator()
        data = make_analyte(ph_min="not_a_number")  # should be float
        result = validator.validate("analyte", data)
        assert not result.is_valid

    def test_out_of_range_value_fails(self):
        """Out-of-range value causes validation failure."""
        validator = UniversalBiosensorValidator()
        data = make_analyte(ph_min=100.0)  # outside 2.0-10.0
        result = validator.validate("analyte", data)
        assert not result.is_valid

    def test_db_uniqueness_check_existing_entity(self):
        """Returns failure when entity already exists in database."""
        mock_db = MagicMock()
        mock_db.entity_exists.return_value = True
        validator = UniversalBiosensorValidator(db=mock_db)
        result = validator.validate("analyte", make_analyte())
        assert not result.is_valid

    def test_db_uniqueness_check_new_entity(self):
        """Passes when entity does not exist in database."""
        mock_db = MagicMock()
        mock_db.entity_exists.return_value = False
        validator = UniversalBiosensorValidator(db=mock_db)
        result = validator.validate("analyte", make_analyte())
        assert result.is_valid

    def test_none_value_fields_are_skipped(self):
        """Fields with None values are skipped in constraint validation."""
        validator = UniversalBiosensorValidator()
        data = make_analyte(ph_min=None)  # None should be skipped
        result = validator.validate("analyte", data)
        # None values shouldn't cause failures
        assert result.is_valid

    def test_pattern_violation_fails(self):
        """ID not matching the required pattern fails validation."""
        validator = UniversalBiosensorValidator()
        data = make_analyte(ta_id="WRONG123")  # must start with TA
        result = validator.validate("analyte", data)
        assert not result.is_valid

    def test_enum_violation_fails(self):
        """Value not in allowed enum fails validation."""
        validator = UniversalBiosensorValidator()
        data = make_immobilization_layer(adhesion="invalid_value")
        result = validator.validate("immobilization", data)
        assert not result.is_valid

    def test_custom_config_is_used(self):
        """Validator uses provided custom config."""
        custom_config = {
            "custom": {
                "required_fields": {"field_a"},
                "constraints": {},
                "id_field": "field_a",
            }
        }
        validator = UniversalBiosensorValidator(config=custom_config)
        result = validator.validate("custom", {"field_a": "value"})
        assert result.is_valid


class TestUniversalCRUDManager:
    """Tests for UniversalCRUDManager."""

    def _make_crud(self, db_mock=None):
        """Helper to create a CRUDManager with mock DB."""
        if db_mock is None:
            db_mock = MagicMock()
            db_mock.entity_exists.return_value = False
        validator = UniversalBiosensorValidator(db=db_mock)
        return UniversalCRUDManager(validator, db_mock), db_mock

    def test_create_valid_entity_succeeds(self):
        """Creating a valid entity returns success."""
        crud, db_mock = self._make_crud()
        db_mock.insert.return_value = True
        success, msg = crud.create("analyte", make_analyte())
        assert success
        assert db_mock.insert.called

    def test_create_invalid_entity_fails(self):
        """Creating an entity with invalid data returns failure."""
        crud, db_mock = self._make_crud()
        success, msg = crud.create("analyte", {})  # empty data, missing required fields
        assert not success
        assert not db_mock.insert.called  # DB should not be called

    def test_create_duplicate_entity_fails(self):
        """Creating a duplicate entity returns failure with appropriate message."""
        crud, db_mock = self._make_crud()
        db_mock.insert.return_value = "DUPLICATE"
        success, msg = crud.create("analyte", make_analyte())
        assert not success
        assert "уже существует" in msg

    def test_create_db_error_fails(self):
        """DB error during insert returns failure."""
        crud, db_mock = self._make_crud()
        db_mock.insert.return_value = "some error"  # not True, not DUPLICATE
        success, msg = crud.create("analyte", make_analyte())
        assert not success

    def test_list_returns_paginated_results(self):
        """list() returns results from DB with pagination."""
        crud, db_mock = self._make_crud()
        db_mock.list_all_paginated.return_value = [{"ta_id": "TA001"}, {"ta_id": "TA002"}]
        result = crud.list("analyte", limit=10, offset=0)
        assert len(result) == 2
        db_mock.list_all_paginated.assert_called_once_with("analyte", 10, 0)

    def test_list_with_default_pagination(self):
        """list() uses default limit=50, offset=0."""
        crud, db_mock = self._make_crud()
        db_mock.list_all_paginated.return_value = []
        crud.list("analyte")
        db_mock.list_all_paginated.assert_called_once_with("analyte", 50, 0)


class TestBiosensorService:
    """Tests for BiosensorService (high-level API)."""

    def _make_service(self, entity_exists=False):
        """Helper to create a BiosensorService with mock DB."""
        mock_db = MagicMock()
        mock_db.entity_exists.return_value = entity_exists
        return BiosensorService(mock_db), mock_db

    def test_validate_entity_valid(self):
        """validate_entity returns valid result for correct data."""
        service, _ = self._make_service()
        result = service.validate_entity("analyte", make_analyte())
        assert result.is_valid

    def test_validate_entity_invalid(self):
        """validate_entity returns invalid result for bad data."""
        service, _ = self._make_service()
        result = service.validate_entity("analyte", {})
        assert not result.is_valid

    def test_save_entity_success(self):
        """save_entity inserts entity and returns success."""
        service, mock_db = self._make_service()
        mock_db.insert.return_value = True
        success, msg = service.save_entity("analyte", make_analyte())
        assert success

    def test_save_entity_failure(self):
        """save_entity returns failure for invalid entity."""
        service, _ = self._make_service()
        success, msg = service.save_entity("analyte", {})
        assert not success

    def test_get_all_entities_returns_list(self):
        """get_all_entities returns list from database."""
        service, mock_db = self._make_service()
        mock_db.list_all_paginated.return_value = [{"ta_id": "TA001"}]
        result = service.get_all_entities("analyte")
        assert isinstance(result, list)
        assert len(result) == 1

    def test_get_all_entities_with_pagination(self):
        """get_all_entities forwards pagination parameters."""
        service, mock_db = self._make_service()
        mock_db.list_all_paginated.return_value = []
        service.get_all_entities("analyte", limit=10, offset=5)
        mock_db.list_all_paginated.assert_called_once_with("analyte", 10, 5)
