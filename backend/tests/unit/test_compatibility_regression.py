import pytest

from domain.validators import CombinationValidator
from tests.factories import make_compatible_four_layers, make_incompatible_four_layers

pytestmark = pytest.mark.unit


def test_legacy_combination_validator_unchanged():
    analyte, bio, im, mem = make_compatible_four_layers()
    a = {
        "PH_Min": analyte["ph_min"],
        "PH_Max": analyte["ph_max"],
        "T_Max": analyte["t_max"],
    }
    b = {
        "PH_Min": bio["ph_min"],
        "PH_Max": bio["ph_max"],
        "T_Min": bio["t_min"],
        "T_Max": bio["t_max"],
    }
    i = {
        "PH_Min": im["ph_min"],
        "PH_Max": im["ph_max"],
        "T_Min": im["t_min"],
        "T_Max": im["t_max"],
        "MP": im["young_modulus"],
    }
    m = {
        "PH_Min": mem["ph_min"],
        "PH_Max": mem["ph_max"],
        "T_Min": mem["t_min"],
        "T_Max": mem["t_max"],
        "MP": mem["young_modulus"],
    }

    ok, reason = CombinationValidator.validate_combination(a, b, i, m)
    assert ok is True
    assert reason is None


def test_existing_tests_still_pass():
    analyte, bio, im, mem = make_incompatible_four_layers("ph")
    a = {
        "PH_Min": analyte["ph_min"],
        "PH_Max": analyte["ph_max"],
        "T_Max": analyte["t_max"],
    }
    b = {
        "PH_Min": bio["ph_min"],
        "PH_Max": bio["ph_max"],
        "T_Min": bio["t_min"],
        "T_Max": bio["t_max"],
    }
    i = {
        "PH_Min": im["ph_min"],
        "PH_Max": im["ph_max"],
        "T_Min": im["t_min"],
        "T_Max": im["t_max"],
        "MP": im["young_modulus"],
    }
    m = {
        "PH_Min": mem["ph_min"],
        "PH_Max": mem["ph_max"],
        "T_Min": mem["t_min"],
        "T_Max": mem["t_max"],
        "MP": mem["young_modulus"],
    }

    ok, reason = CombinationValidator.validate_combination(a, b, i, m)
    assert ok is False
    assert reason is not None
