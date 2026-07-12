from services.combination_synthesis import CombinationSynthesisService
from domain.validators import CombinationValidator


def test_check_ph_compatibility_skips_missing_values():
    ok, msg = CombinationValidator.check_ph_compatibility(None, 7.0, (3.0, 4.0))
    assert ok is True
    assert msg is None


def test_check_mechanical_compatibility_skips_missing_values():
    ok, msg = CombinationValidator.check_mechanical_compatibility(None, 100.0)
    assert ok is True
    assert msg is None


def test_calculate_score_handles_none_metrics():
    metrics = {
        "SN_total": None,
        "RP_total": None,
        "ST_total": None,
        "HL_total": None,
        "DR_total": None,
        "TR_total": None,
        "LOD_total": None,
        "PC_total": None,
    }
    score = CombinationSynthesisService._calculate_score(metrics)
    assert 0.0 <= score <= 10.0
