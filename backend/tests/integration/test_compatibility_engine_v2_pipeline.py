import pytest

from domain.compatibility import CompatibilityEngineV2

pytestmark = pytest.mark.integration


def _base_glucose_structure() -> dict:
    return {
        "TA": {"TA_ID": "TA_GLU", "PH_Min": 5.5, "PH_Max": 8.0, "T_Max": 42.0},
        "BRE": {"BRE_ID": "BRE_AB", "PH_Min": 6.0, "PH_Max": 8.0, "T_Min": 15.0, "T_Max": 40.0, "TR": 5.0},
        "IM": {
            "IM_ID": "IM_PDMS",
            "PH_Min": 5.5,
            "PH_Max": 8.5,
            "T_Min": 12.0,
            "T_Max": 41.0,
            "MP": 8.0,
            "Adh_IM": 0.9,
            "Sol_IM": 6.0,
            "TR": 4.0,
            "PC": 2.0,
        },
        "MEM": {"MEM_ID": "MEM_OX", "PH_Min": 5.0, "PH_Max": 8.5, "T_Min": 10.0, "T_Max": 42.0, "MP": 8.2, "TR": 3.0, "PC": 3.0},
        "iso_10993": True,
        "temperature_resistant": True,
        "pdms_compatible": True,
        "leakage_ul": 0.3,
        "stability_months": 7.5,
        "TR_total": 12.0,
        "PC_total": 8.0,
    }


def _base_vegf_structure() -> dict:
    s = _base_glucose_structure()
    s["TA"] = {"TA_ID": "TA_VEGF", "PH_Min": 6.2, "PH_Max": 7.6, "T_Max": 44.0}
    s["BRE"]["PH_Min"] = 6.3
    s["BRE"]["PH_Max"] = 7.5
    s["BRE"]["T_Max"] = 38.0
    s["IM"]["PH_Min"] = 6.2
    s["IM"]["PH_Max"] = 7.8
    s["IM"]["T_Max"] = 39.0
    s["MEM"]["PH_Min"] = 6.0
    s["MEM"]["PH_Max"] = 7.8
    s["MEM"]["T_Max"] = 40.0
    s["TR_total"] = 10.0
    s["PC_total"] = 7.0
    return s


def test_full_validation_pipeline_glucose_biosensor():
    engine = CompatibilityEngineV2()
    structure = _base_glucose_structure()

    stage1_ok, stage1_failed = engine.validate_stage1(structure)
    stage2_ok, stage2_failed = engine.validate_stage2(structure, "PoC")

    assert stage1_ok is True
    assert stage1_failed == []
    assert stage2_ok is True
    assert stage2_failed == []


def test_full_validation_pipeline_vegf_biosensor():
    engine = CompatibilityEngineV2()
    structure = _base_vegf_structure()

    stage1_ok, stage1_failed = engine.validate_stage1(structure)
    stage2_ok, stage2_failed = engine.validate_stage2(structure, "Clinical_Diagnostics")

    assert stage1_ok is True
    assert stage1_failed == []
    assert stage2_ok is True
    assert stage2_failed == []


def test_zero_false_negatives_on_reference_structures():
    engine = CompatibilityEngineV2()
    references = [_base_glucose_structure(), _base_vegf_structure()]

    for structure in references:
        stage1_ok, stage1_failed = engine.validate_stage1(structure)
        assert stage1_ok is True, f"Unexpected Stage1 failure: {stage1_failed}"
