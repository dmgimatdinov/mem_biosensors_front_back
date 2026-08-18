import math

import pytest

from domain.analytics import (
    StabilityAnalysis,
    ahp_calculate_weights,
    ahp_check_consistency,
    epsilon_constraints_optimize,
    pareto_frontier,
    topsis_rank,
)
from domain.analytics import calculate_score
from services.score_normalizer import calculate_score as legacy_calculate_score


def test_ahp_equal_comparisons():
    matrix = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    weights = ahp_calculate_weights(matrix)
    assert weights == [pytest.approx(1 / 3), pytest.approx(1 / 3), pytest.approx(1 / 3)]


def test_pareto_frontier_simple_case():
    structures = [
        {"id": "A", "LoD": 5, "ST": 80},
        {"id": "B", "LoD": 7, "ST": 75},
        {"id": "C", "LoD": 6, "ST": 85},
    ]
    frontier = pareto_frontier(structures, ["LoD", "ST"])
    ids = [s["id"] for s in frontier]
    assert "B" not in ids
    assert set(ids) <= {"A", "C"}


def test_topsis_two_structures_clear_winner():
    structures = [
        {"id": "A", "SN": 100, "TR": 60},
        {"id": "B", "SN": 120, "TR": 20},
    ]
    ranked = topsis_rank(structures, ["SN", "TR"], [0.6, 0.4])
    assert ranked[0][0]["id"] == "B"
    assert ranked[0][1] > ranked[1][1]


def test_epsilon_constraints_respects_all_limits():
    structures = [
        {"id": "A", "LoD": 8, "TR": 20},
        {"id": "B", "LoD": 9, "TR": 25},
        {"id": "C", "LoD": 12, "TR": 35},
    ]
    result = epsilon_constraints_optimize(structures, "SN", {"LoD": ("<", 10), "TR": ("<", 30)})
    assert len(result) == 2
    assert all(s["LoD"] < 10 for s in result)
    assert all(s["TR"] < 30 for s in result)


def test_stress_test_stable_structure():
    structures = [
        {"id": "A", "SN": 5000, "TR": 100, "ST": 300, "RP": 0.95, "LoD": 5},
        {"id": "B", "SN": 4000, "TR": 200, "ST": 250, "RP": 0.9, "LoD": 6},
        {"id": "C", "SN": 3900, "TR": 220, "ST": 240, "RP": 0.88, "LoD": 7},
    ]
    analysis = StabilityAnalysis().run(structures, [0.4, 0.2, 0.2, 0.2], n_simulations=50, seed=7)
    assert analysis["A"]["stability_label"] == "stable"


def test_sensitivity_detects_low_reliability():
    structures = [
        {"id": "A", "SN": 5000, "TR": 100, "ST": 300, "RP": 0.95, "LoD": 5, "reliability_category": "low"},
        {"id": "B", "SN": 4800, "TR": 110, "ST": 290, "RP": 0.92, "LoD": 6, "reliability_category": "high"},
        {"id": "C", "SN": 4600, "TR": 115, "ST": 280, "RP": 0.90, "LoD": 7, "reliability_category": "high"},
        {"id": "D", "SN": 4400, "TR": 120, "ST": 270, "RP": 0.88, "LoD": 8, "reliability_category": "high"},
        {"id": "E", "SN": 4200, "TR": 125, "ST": 260, "RP": 0.86, "LoD": 9, "reliability_category": "high"},
        {"id": "F", "SN": 4000, "TR": 130, "ST": 250, "RP": 0.84, "LoD": 10, "reliability_category": "high"},
    ]
    result = StabilityAnalysis().sensitivity_to_uncertainty(structures)
    assert "requires_experimental_check" in result["A"]["flags"]


def test_facade_weighted_sum_backward_compatible():
    structure = {"SN_total": 10000, "TR_total": 1000, "ST_total": 100, "LOD_total": 1000, "DR_total": 100, "PC_total": 100}
    assert calculate_score([structure], method="weighted_sum") == pytest.approx(legacy_calculate_score(structure))
