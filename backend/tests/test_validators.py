# tests/test_validators.py

import pytest
from domain.validators import DataValidator
from domain.models import Analyte, BioRecognitionLayer

def test_validate_analyte_valid():
    """Тест валидного аналита."""
    analyte = Analyte(
        ta_id="TA001",
        ta_name="Glucose",
        ph_min=5.0,
        ph_max=8.0,
        t_max=50.0
    )
    is_valid, error = DataValidator.validate_analyte(analyte)
    assert is_valid == True
    assert error is None

def test_validate_analyte_invalid_ph_range():
    """Тест: pH_min > pH_max."""
    analyte = Analyte(
        ta_id="TA002",
        ta_name="Invalid",
        ph_min=9.0,
        ph_max=5.0  # Неправильно!
    )
    is_valid, error = DataValidator.validate_analyte(analyte)
    assert is_valid == False
    assert "pH_min не может быть больше pH_max" in error

def test_validate_analyte_missing_id():
    """Тест: отсутствует ID."""
    analyte = Analyte(
        ta_id="",  # Пусто!
        ta_name="No ID"
    )
    is_valid, error = DataValidator.validate_analyte(analyte)
    assert is_valid == False
    assert "обязательны" in error

def test_validate_bio_layer_valid():
    """Тест валидного биослоя."""
    bio = BioRecognitionLayer(
        bre_id="BRE001",
        bre_name="Antibody",
        t_min=10.0,
        t_max=40.0
    )
    is_valid, error = DataValidator.validate_bio_recognition_layer(bio)
    assert is_valid == True
