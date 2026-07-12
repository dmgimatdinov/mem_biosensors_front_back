import pytest

from domain.metrics import (
    calculate_final_score,
    calculate_interval_score,
    calculate_reliability_coefficient,
    suggest_critical_gaps,
)

pytestmark = pytest.mark.unit


def test_reliability_coefficient_high_completeness():
    kappa = calculate_reliability_coefficient(eta=0.9, alpha=0.3, gamma=2.0)
    assert kappa == pytest.approx(0.97, abs=0.04)


def test_reliability_coefficient_low_completeness():
    kappa = calculate_reliability_coefficient(eta=0.6, alpha=0.7, gamma=2.0)
    assert kappa == pytest.approx(0.55, abs=0.05)


def test_reliability_coefficient_nonlinear_penalty():
    k_09 = calculate_reliability_coefficient(eta=0.9, alpha=0.7, gamma=2.0)
    k_08 = calculate_reliability_coefficient(eta=0.8, alpha=0.7, gamma=2.0)
    drop_90_80 = (k_09 - k_08) / k_09

    k_07 = calculate_reliability_coefficient(eta=0.7, alpha=0.7, gamma=4.0)
    k_06 = calculate_reliability_coefficient(eta=0.6, alpha=0.7, gamma=4.0)
    drop_70_60 = (k_07 - k_06) / k_07

    assert 0.10 <= drop_90_80 <= 0.15
    assert 0.30 <= drop_70_60 <= 0.40


def test_final_score_with_reliability():
    assert calculate_final_score(raw_score=8.0, kappa=0.75) == pytest.approx(6.0)


def test_interval_score_pessimistic_strategy():
    structure = {
        "sn_total": 1500.0,
        "tr_total": None,
        "st_total": 120.0,
    }
    score_min, score_max, _ = calculate_interval_score(structure, strategy="pessimistic")
    assert score_min <= score_max


def test_interval_score_optimistic_strategy():
    structure = {
        "sn_total": 1500.0,
        "lod_total": None,
        "dr_total": 350.0,
    }
    score_min, score_max, _ = calculate_interval_score(structure, strategy="optimistic")
    assert score_min <= score_max


def test_interval_score_average_strategy():
    structure = {
        "sn_total": None,
        "tr_total": None,
        "st_total": 180.0,
        "lod_total": None,
    }
    score_min, score_max, _ = calculate_interval_score(structure, strategy="average")
    assert score_min <= score_max


def test_interval_score_delta_positive():
    structure = {
        "sn_total": None,
        "tr_total": None,
        "st_total": 120.0,
        "dr_total": None,
    }
    score_min, score_max, delta = calculate_interval_score(structure, strategy="average")
    assert score_min <= score_max
    assert delta >= 0


def test_suggest_critical_gaps_returns_empty_for_high_kappa():
    structure = {
        "analyte": {"data_completeness": 0.95, "reliability_category": "high"},
        "bio_layer": {"data_completeness": 0.95, "reliability_category": "high"},
        "immobilization_layer": {"data_completeness": 0.95, "reliability_category": "high"},
        "memristive_layer": {"data_completeness": 0.95, "reliability_category": "high"},
        "sn_total": 1800.0,
        "tr_total": 300.0,
        "st_total": 140.0,
        "lod_total": 900.0,
        "dr_total": 300.0,
        "pc_total": 250.0,
    }
    assert suggest_critical_gaps(structure) == []


def test_suggest_critical_gaps_returns_prioritized_list():
    structure = {
        "analyte": {"data_completeness": 0.30, "reliability_category": "low"},
        "bio_layer": {"data_completeness": 0.40, "reliability_category": "low"},
        "immobilization_layer": {"data_completeness": 0.35, "reliability_category": "medium"},
        "memristive_layer": {"data_completeness": 0.25, "reliability_category": "low"},
        "st_total": 100.0,
    }

    gaps = suggest_critical_gaps(structure)
    assert isinstance(gaps, list)
    assert gaps
    impacts = [item["impact"] for item in gaps]
    assert impacts == sorted(impacts, reverse=True)
    for item in gaps:
        assert {"parameter", "priority", "impact", "method", "effort"}.issubset(item.keys())
