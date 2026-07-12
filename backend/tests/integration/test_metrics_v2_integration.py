import pytest

import settings
from domain.metrics import calculate_combination_metrics
from domain.metrics_v1 import calculate_combination_metrics as calculate_combination_metrics_v1
from tests.factories import make_compatible_four_layers

pytestmark = pytest.mark.integration


def _to_upper(analyte, bio, immob, mem):
    return (
        {
            "ST": analyte["stability"],
            "TA_ID": analyte["ta_id"],
        },
        {
            "SN": bio["sensitivity"],
            "TR": bio["response_time"],
            "ST": bio["stability"],
            "LOD": bio["lod"],
            "DR_Min": bio["dr_min"],
            "DR_Max": bio["dr_max"],
            "RP": bio["reproducibility"],
            "HL": bio["durability"],
            "K_M": 10.0,
        },
        {
            "K_IM": immob["loss_coefficient"],
            "TR": immob["response_time"],
            "ST": immob["stability"],
            "RP": immob["reproducibility"],
            "HL": immob["durability"],
            "d_IM": 1.0,
            "D_eff": 2.0,
        },
        {
            "SN": mem["sensitivity"],
            "TR": mem["response_time"],
            "ST": mem["stability"],
            "LOD": mem["lod"],
            "DR_Min": mem["dr_min"],
            "DR_Max": mem["dr_max"],
            "RP": mem["reproducibility"],
            "HL": mem["durability"],
            "I_read": 5.0,
            "SNR_MEM": 10.0,
            "CV": 0.1,
        },
    )


def test_end_to_end_metrics_calculation_glucose(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "METRICS_VERSION", "v2")
    analyte, bio, immob, mem = make_compatible_four_layers()
    ta, bre, im, me = _to_upper(analyte, bio, immob, mem)

    metrics = calculate_combination_metrics(ta, bre, im, me)
    assert metrics["SN_total"] > 0
    assert metrics["TR_total"] > 0
    assert metrics["LOD_total"] > 0
    assert metrics["DR_total"] > 0
    assert metrics["ST_total"] > 0


def test_end_to_end_metrics_calculation_vegf(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "METRICS_VERSION", "v2")
    analyte, bio, immob, mem = make_compatible_four_layers()
    bio["sensitivity"] = 650
    bio["response_time"] = 40
    mem["sensitivity"] = 700
    mem["response_time"] = 15
    ta, bre, im, me = _to_upper(analyte, bio, immob, mem)
    me["CV"] = 0.2

    metrics = calculate_combination_metrics(ta, bre, im, me)
    assert metrics["RP_total"] == pytest.approx(5.0)
    assert metrics["SN_total"] > 0


def test_regression_v1_results_unchanged(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "METRICS_VERSION", "v1")
    analyte, bio, immob, mem = make_compatible_four_layers()
    ta, bre, im, me = _to_upper(analyte, bio, immob, mem)

    metrics_facade = calculate_combination_metrics(ta, bre, im, me)
    metrics_direct = calculate_combination_metrics_v1(ta, bre, im, me)
    assert metrics_facade == metrics_direct
