import pytest

from domain.compatibility import CompatibilityEngineV2

pytestmark = pytest.mark.unit


def _valid_structure() -> dict:
    return {
        "TA": {"PH_Min": 5.0, "PH_Max": 8.5, "T_Max": 45.0, "PC": 2.0},
        "BRE": {"PH_Min": 6.0, "PH_Max": 8.0, "T_Min": 15.0, "T_Max": 40.0, "TR": 8.0},
        "IM": {
            "PH_Min": 5.5,
            "PH_Max": 8.5,
            "T_Min": 12.0,
            "T_Max": 42.0,
            "MP": 10.0,
            "Adh_IM": 0.8,
            "Sol_IM": 6.0,
            "TR": 4.0,
            "PC": 2.0,
        },
        "MEM": {"PH_Min": 5.0, "PH_Max": 8.5, "T_Min": 10.0, "T_Max": 45.0, "MP": 10.2, "TR": 2.0, "PC": 3.0},
        "iso_10993": True,
        "temperature_resistant": True,
        "pdms_compatible": True,
        "leakage_ul": 0.2,
        "stability_months": 8.0,
        "TR_total": 12.0,
        "PC_total": 9.0,
    }


def test_pH_compatibility_valid_range():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    ok, reason = engine.check_pH_compatibility(s["TA"], s["BRE"], s["IM"], s["MEM"])
    assert ok is True
    assert reason is None


def test_pH_compatibility_no_overlap():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["BRE"]["PH_Min"] = 7.0
    s["BRE"]["PH_Max"] = 8.5
    s["MEM"]["PH_Min"] = 5.0
    s["MEM"]["PH_Max"] = 6.5

    ok, reason = engine.check_pH_compatibility(s["TA"], s["BRE"], s["IM"], s["MEM"])
    assert ok is False
    assert reason == "pH-несовместимость: BRE требует pH 7.0-8.5, MEM работает при pH 5.0-6.5"


def test_analyte_thermal_stability_pass():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    ok, reason = engine.check_analyte_thermal_stability(s["TA"], s["BRE"], s["IM"], s["MEM"])
    assert ok is True
    assert reason is None


def test_analyte_thermal_stability_degradation():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["TA"]["T_Max"] = 35.0
    ok, reason = engine.check_analyte_thermal_stability(s["TA"], s["BRE"], s["IM"], s["MEM"])
    assert ok is False
    assert "Термическая деградация аналита" in reason


def test_layer_temperature_compatibility():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    ok, reason = engine.check_layer_temperature_compatibility(s["BRE"], s["IM"], s["MEM"])
    assert ok is True
    assert reason is None


def test_mechanical_compatibility_within_delta():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    ok, reason = engine.check_mechanical_compatibility(s["IM"], s["MEM"], delta_max=0.5)
    assert ok is True
    assert reason is None


def test_mechanical_compatibility_exceeds_delta():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["IM"]["MP"] = 10.0
    s["MEM"]["MP"] = 12.3
    ok, reason = engine.check_mechanical_compatibility(s["IM"], s["MEM"], delta_max=0.5)
    assert ok is False
    assert "|MP_IM - MP_MEM| = 2.3 ГПа" in reason


def test_adhesion_below_minimum():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["IM"]["Adh_IM"] = 0.3
    ok, reason = engine.check_adhesion_solubility(s["IM"], adh_min=0.5, sol_max=10.0)
    assert ok is False
    assert "Низкая адгезия" in reason


def test_solubility_above_maximum():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["IM"]["Sol_IM"] = 11.0
    ok, reason = engine.check_adhesion_solubility(s["IM"], adh_min=0.5, sol_max=10.0)
    assert ok is False
    assert "Высокая растворимость" in reason


def test_stage2_poc_power_consumption():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["PC_total"] = 15.0
    ok, failed = engine.validate_stage2(s, "PoC")
    assert ok is False
    assert any("энергопотребление" in item for item in failed)


def test_stage2_loc_pdms_compatibility():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["pdms_compatible"] = False
    ok, failed = engine.validate_stage2(s, "LoC")
    assert ok is False
    assert any("PDMS" in item for item in failed)


def test_stage2_clinical_response_time():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["TR_total"] = 16.0
    ok, failed = engine.validate_stage2(s, "Clinical_Diagnostics")
    assert ok is False
    assert any("TR" in item for item in failed)


def test_early_termination_on_pH_failure():
    engine = CompatibilityEngineV2()
    s = _valid_structure()
    s["BRE"]["PH_Min"] = 9.0
    s["BRE"]["PH_Max"] = 10.0

    ok, failed = engine.validate_stage1(s)
    assert ok is False
    assert failed
    assert engine.last_stage1_trace == ["check_pH_compatibility"]


def test_compatibility_index_reduces_search_space():
    engine = CompatibilityEngineV2()
    s = _valid_structure()

    analytes = [s["TA"], {**s["TA"], "PH_Min": 4.5, "PH_Max": 8.0}]
    bio_layers = [s["BRE"], {**s["BRE"], "T_Min": 60.0, "T_Max": 80.0}]
    immob_layers = [s["IM"], {**s["IM"], "IM_ID": "IM_BAD", "Adh_IM": 0.2}]
    mem_layers = [s["MEM"], {**s["MEM"], "MEM_ID": "MEM_BAD", "MP": 20.0}]

    result = engine.build_compatibility_index(analytes, bio_layers, immob_layers, mem_layers)
    assert result["complexity"]["before"] == "O(N^4)"
    assert result["complexity"]["after"] == "O(N^2 * k)"
    assert result["complexity"]["indexed_candidates"] < result["complexity"]["baseline_candidates"]
