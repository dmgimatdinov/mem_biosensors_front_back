import pytest

import settings
from domain import metrics_v1
from domain.metrics import (
    calculate_combination_metrics,
    calculate_dynamic_range,
    calculate_half_life,
    calculate_lod,
    calculate_reproducibility,
    calculate_response_time,
    calculate_sensitivity,
    calculate_stability,
    compute_data_completeness_vector,
    normalize_metric,
)

pytestmark = pytest.mark.unit


def _switch_version(monkeypatch: pytest.MonkeyPatch, version: str) -> None:
    monkeypatch.setattr(settings, "METRICS_VERSION", version)


def test_sensitivity_formula_v2(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre = {"SN_BRE": 2.0}
    mem = {"SN_MEM": 3.0}
    immob = {"K_IM": 4.0}
    assert calculate_sensitivity(bre, mem, immob) == pytest.approx(24.0)


def test_response_time_with_diffusion(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre = {"TR_BRE": 4.0}
    immob = {"d_IM": 2.0, "D_eff": 2.0}
    mem = {"TR_MEM": 3.0}
    # 4 + (2^2 / 2) + 3 = 9
    assert calculate_response_time(bre, immob, mem) == pytest.approx(9.0)


def test_response_time_dominant_bre_kinetics(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre = {"TR_BRE": 40.0}
    immob = {"d_IM": 1.0, "D_eff": 10.0}
    mem = {"TR_MEM": 2.0}
    tr = calculate_response_time(bre, immob, mem)
    assert tr > 42.0
    assert (bre["TR_BRE"]) > ((immob["d_IM"] ** 2) / immob["D_eff"])


def test_response_time_dominant_diffusion(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre = {"TR_BRE": 2.0}
    immob = {"d_IM": 10.0, "D_eff": 1.0}
    mem = {"TR_MEM": 2.0}
    tr = calculate_response_time(bre, immob, mem)
    assert tr == pytest.approx(104.0)


def test_stability_includes_analyte(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    ta = {"ST_TA": 10.0}
    bre = {"ST_BRE": 30.0}
    immob = {"ST_IM": 40.0}
    mem = {"ST_MEM": 20.0}
    assert calculate_stability(ta, bre, immob, mem) == pytest.approx(10.0)


def test_stability_weak_link_principle(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    ta = {"ST_TA": 50.0}
    bre = {"ST_BRE": 20.0}
    immob = {"ST_IM": 60.0}
    mem = {"ST_MEM": 55.0}
    assert calculate_stability(ta, bre, immob, mem) == pytest.approx(20.0)


def test_lod_with_noise(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre = {"SN_BRE": 2.0}
    mem = {"SN_MEM": 3.0, "I_read": 9.0, "SNR_MEM": 3.0}
    immob = {"K_IM": 1.0}
    lod = calculate_lod(bre, mem, immob=immob)
    # sigma_noise = 9/3 = 3, LoD = 3*sigma/SN = 9/6 = 1.5
    assert lod == pytest.approx(1.5)


def test_dynamic_range_from_michaelis_constant(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre = {"K_M": 20.0}
    mem = {}
    dr = calculate_dynamic_range(bre, mem, lod=2.0)
    assert dr == pytest.approx(100.0)


def test_reproducibility_from_cv(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre, immob, mem = {}, {}, {"CV": 0.1}
    rp = calculate_reproducibility(bre, immob, mem)
    assert rp == pytest.approx(10.0)


def test_half_life_minimum_principle(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    bre = {"HL_BRE": 1000.0}
    immob = {"HL_IM": 700.0}
    mem = {"HL_MEM": 900.0}
    assert calculate_half_life(bre, immob, mem) == pytest.approx(700.0)


def test_normalization_greater_is_better(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    assert normalize_metric(70.0, 0.0, 100.0, greater_is_better=True) == pytest.approx(0.7)


def test_normalization_lesser_is_better(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    assert normalize_metric(20.0, 0.0, 100.0, greater_is_better=False) == pytest.approx(0.8)


def test_normalization_user_defined_bounds(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    assert normalize_metric(35.0, 10.0, 50.0, greater_is_better=True) == pytest.approx(0.625)


def test_data_completeness_full(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    structure = {
        "SN_BRE": 1,
        "SN_MEM": 1,
        "K_IM": 1,
        "d_IM": 1,
        "D_eff": 1,
        "TR_BRE": 1,
        "TR_MEM": 1,
        "ST_TA": 1,
        "ST_BRE": 1,
        "ST_IM": 1,
        "ST_MEM": 1,
        "I_read": 1,
        "SNR_MEM": 1,
        "K_M": 1,
        "CV": 1,
        "HL_BRE": 1,
        "HL_IM": 1,
        "HL_MEM": 1,
    }
    _, eta, label = compute_data_completeness_vector(structure)
    assert 0 <= eta <= 1
    assert eta == pytest.approx(1.0)
    assert label == "full"


def test_data_completeness_partial(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    structure = {
        "SN_BRE": 1,
        "SN_MEM": 1,
        "K_IM": 1,
        "d_IM": 1,
        "D_eff": 1,
        "TR_BRE": 1,
        "TR_MEM": 1,
        "ST_TA": 1,
        "ST_BRE": 1,
        "ST_IM": 1,
        "ST_MEM": 1,
    }
    _, eta, label = compute_data_completeness_vector(structure)
    assert 0 <= eta <= 1
    assert 0.6 <= eta < 0.9
    assert label == "partial"


def test_data_completeness_critical(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    structure = {
        "SN_BRE": 1,
        "SN_MEM": 1,
        "K_IM": 1,
        "TR_BRE": 1,
        "TR_MEM": 1,
    }
    _, eta, label = compute_data_completeness_vector(structure)
    assert 0 <= eta <= 1
    assert eta < 0.6
    assert label == "critical"


def test_metrics_version_switch_v1(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v1")
    ta = {"ST": 5.0}
    bre = {"ST": 30.0, "SN": 2.0}
    im = {"ST": 40.0, "K_IM": 0.5}
    mem = {"ST": 20.0, "SN": 3.0}
    # v1 ignores ST_TA and uses legacy formula for SN.
    assert calculate_stability(ta, bre, im, mem) == pytest.approx(20.0)
    assert calculate_sensitivity(bre, mem, im) == pytest.approx(3.0)


def test_metrics_version_switch_v2(monkeypatch: pytest.MonkeyPatch):
    _switch_version(monkeypatch, "v2")
    ta = {"ST_TA": 5.0}
    bre = {"ST_BRE": 30.0, "SN_BRE": 2.0}
    im = {"ST_IM": 40.0, "K_IM": 0.5}
    mem = {"ST_MEM": 20.0, "SN_MEM": 3.0}
    assert calculate_stability(ta, bre, im, mem) == pytest.approx(5.0)
    assert calculate_sensitivity(bre, mem, im) == pytest.approx(3.0)
