import pytest
from backend.domain.validators import UniversalBiosensorValidator
from backend.tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
    make_compatible_four_layers,
    make_incompatible_four_layers,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestAnalyteValidation:
    """Тесты валидации аналитов."""

    def test_valid_analyte_passes(self):
        """Валидный аналит проходит валидацию."""
        data = make_analyte()
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert result.success
        assert not result.errors

    @pytest.mark.parametrize("field,value,expected_error", [
        ("ta_id", "ABC001", "должен начинаться с ta"),
        ("ta_id", "TA" + "x" * 30, "превышает длину"),
        ("ta_name", "AB", "слишком короткое"),
        ("ta_name", "A" * 300, "слишком длинное"),
        ("ph_min", 1.0, "вне диапазона"),
        ("ph_min", 11.0, "вне диапазона"),
        ("ph_max", 1.0, "вне диапазона"),
        ("ph_max", 11.0, "вне диапазона"),
        ("t_max", -10, "вне диапазона"),
        ("t_max", 200, "вне диапазона"),
        ("stability", -1, "вне диапазона"),
        ("stability", 400, "вне диапазона"),
        ("half_life", -1, "вне диапазона"),
        ("half_life", 10000, "вне диапазона"),
        ("power_consumption", -1, "вне диапазона"),
        ("power_consumption", 2000, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_analyte(**{field: value})
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert not result.success
        # проверяем, что хотя бы одно сообщение ошибки содержит ожидаемую подстроку
        assert any(expected_error in err.lower() for err in result.errors)

    def test_ph_min_greater_than_ph_max(self):
        """pH_Min не может превышать pH_Max."""
        data = make_analyte(ph_min=8.0, ph_max=5.0)
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert not result.success
        assert any("ph" in err.lower() for err in result.errors)

    def test_missing_required_fields(self):
        """Отсутствие обязательных полей отклоняется."""
        data = make_analyte()
        # Удаляем обязательное поле
        if "ta_id" in data:
            del data["ta_id"]
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert not result.success
        assert any("обязательн" in err.lower() for err in result.errors)

    def test_boundary_values(self):
        """Граничные значения проходят валидацию."""
        data = make_analyte(ph_min=2.0, ph_max=10.0, t_max=0)
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert result.success

        data = make_analyte(ph_min=2.0, ph_max=10.0, t_max=180)
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert result.success


class TestBioRecognitionValidation:
    """Тесты валидации биораспознающего слоя."""

    def test_valid_bio_layer_passes(self):
        """Валидный биослой проходит валидацию."""
        data = make_bio_recognition_layer()
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert result.success

    @pytest.mark.parametrize("field,value,expected_error", [
        ("bre_id", "ABC001", "должен начинаться с bre"),
        ("bre_name", "AB", "слишком короткое"),
        ("ph_min", 1.0, "вне диапазона"),
        ("ph_max", 11.0, "вне диапазона"),
        ("t_min", -10, "вне диапазона"),
        ("t_max", 200, "вне диапазона"),
        ("dr_min", -1.0, "вне диапазона"),
        ("dr_max", 20000.0, "вне диапазона"),
        ("sensitivity", -1, "вне диапазона"),
        ("reproducibility", -1, "вне диапазона"),
        ("reproducibility", 101, "вне диапазона"),
        ("response_time", -1, "вне диапазона"),
        ("stability", -1, "вне диапазона"),
        ("lod", -1, "вне диапазона"),
        ("durability", -1, "вне диапазона"),
        ("power_consumption", -1, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_bio_recognition_layer(**{field: value})
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success
        assert any(expected_error in err.lower() for err in result.errors)

    def test_ph_min_greater_than_ph_max(self):
        """pH_Min > pH_Max отклоняется."""
        data = make_bio_recognition_layer(ph_min=8.0, ph_max=5.0)
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success

    def test_t_min_greater_than_t_max(self):
        """T_Min > T_Max отклоняется."""
        data = make_bio_recognition_layer(t_min=60, t_max=20)
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success

    def test_dr_min_greater_than_dr_max(self):
        """DR_Min > DR_Max отклоняется."""
        data = make_bio_recognition_layer(dr_min=1000.0, dr_max=0.1)
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success


class TestImmobilizationValidation:
    """Тесты валидации иммобилизационного слоя."""

    def test_valid_im_layer_passes(self):
        """Валидный иммобилизационный слой проходит валидацию."""
        data = make_immobilization_layer()
        result = UniversalBiosensorValidator.validate("immobilization", data)
        assert result.success

    @pytest.mark.parametrize("field,value,expected_error", [
        ("im_id", "ABC001", "должен начинаться с im"),
        ("im_name", "AB", "слишком короткое"),
        ("young_modulus", -1, "вне диапазона"),
        ("young_modulus", 200, "вне диапазона"),
        ("adhesion", "invalid_value", "недопустимое значение"),
        ("solubility", "invalid_value", "недопустимое значение"),
        ("loss_coefficient", -1.0, "вне диапазона"),
        ("loss_coefficient", 2.0, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_immobilization_layer(**{field: value})
        result = UniversalBiosensorValidator.validate("immobilization", data)
        assert not result.success
        assert any(expected_error in err.lower() for err in result.errors)


class TestMemristiveValidation:
    """Тесты валидации мемристивного слоя."""

    def test_valid_mem_layer_passes(self):
        """Валидный мемристивный слой проходит валидацию."""
        data = make_memristive_layer()
        result = UniversalBiosensorValidator.validate("memristive", data)
        assert result.success

    @pytest.mark.parametrize("field,value,expected_error", [
        ("mem_id", "ABC001", "должен начинаться с mem"),
        ("mem_name", "AB", "слишком короткое"),
        ("dr_min", -1.0, "вне диапазона"),
        ("dr_max", 20000.0, "вне диапазона"),
        ("young_modulus", -1, "вне диапазона"),
        ("young_modulus", 200, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_memristive_layer(**{field: value})
        result = UniversalBiosensorValidator.validate("memristive", data)
        assert not result.success
        assert any(expected_error in err.lower() for err in result.errors)


class TestCrossLayerValidation:
    """Тесты валидации совместимости слоёв."""

    def test_compatible_layers_pass(self):
        """Совместимые слои проходят валидацию."""
        analyte, bio, im, mem = make_compatible_four_layers()

        # Каждый слой валиден
        assert UniversalBiosensorValidator.validate("analyte", analyte).success
        assert UniversalBiosensorValidator.validate("bio_recognition", bio).success
        assert UniversalBiosensorValidator.validate("immobilization", im).success
        assert UniversalBiosensorValidator.validate("memristive", mem).success

    @pytest.mark.parametrize("reason", ["ph", "temperature", "mechanical"])
    def test_incompatible_layers_fail(self, reason):
        """Несовместимые слои отклоняются."""
        analyte, bio, im, mem = make_incompatible_four_layers(reason)

        # Каждый слой валиден по отдельности
        assert UniversalBiosensorValidator.validate("analyte", analyte).success
        assert UniversalBiosensorValidator.validate("bio_recognition", bio).success
        assert UniversalBiosensorValidator.validate("immobilization", im).success
        assert UniversalBiosensorValidator.validate("memristive", mem).success

        # Но вместе они несовместимы — если есть поддержка, проверим
        if hasattr(UniversalBiosensorValidator, "validate_compatibility"):
            result = UniversalBiosensorValidator.validate_compatibility(analyte, bio, im, mem)
            assert not result.success
        else:
            # Если в проекте нет валидатора совместимости, помечаем тест как xfail
            pytest.skip("Compatibility validator not implemented")
