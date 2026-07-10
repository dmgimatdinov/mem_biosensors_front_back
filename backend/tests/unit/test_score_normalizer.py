import pytest

from services.score_normalizer import calculate_score
from tests.factories import generate_random_metrics

pytestmark = pytest.mark.unit


class TestScoreNormalizer:
    def test_score_range(self):
        """Score всегда в диапазоне [0, 10]."""
        for _ in range(100):
            metrics = generate_random_metrics()
            score = calculate_score(metrics)
            assert 0 <= score <= 10

    def test_score_monotonicity_sn(self):
        """При увеличении SN Score не уменьшается."""
        metrics1 = {
            "sn_total": 100,
            "tr_total": 100,
            "st_total": 100,
            "lod_total": 100,
            "dr_total": 100,
            "pc_total": 100,
        }
        metrics2 = {
            "sn_total": 200,
            "tr_total": 100,
            "st_total": 100,
            "lod_total": 100,
            "dr_total": 100,
            "pc_total": 100,
        }

        score1 = calculate_score(metrics1)
        score2 = calculate_score(metrics2)
        assert score2 >= score1

    def test_score_monotonicity_tr(self):
        """При увеличении TR Score не увеличивается (штраф)."""
        metrics1 = {
            "sn_total": 100,
            "tr_total": 50,
            "st_total": 100,
            "lod_total": 100,
            "dr_total": 100,
            "pc_total": 100,
        }
        metrics2 = {
            "sn_total": 100,
            "tr_total": 100,
            "st_total": 100,
            "lod_total": 100,
            "dr_total": 100,
            "pc_total": 100,
        }

        score1 = calculate_score(metrics1)
        score2 = calculate_score(metrics2)
        assert score2 <= score1

    def test_perfect_combo_score(self):
        """Идеальная комбинация даёт Score ≈ 10."""
        perfect_metrics = {
            "sn_total": 20000,
            "tr_total": 1,
            "st_total": 365,
            "lod_total": 1,
            "dr_total": 1000,
            "pc_total": 100,
        }
        score = calculate_score(perfect_metrics)
        assert score >= 9.5

    def test_worst_combo_score(self):
        """Худшая комбинация даёт Score ≈ 0."""
        worst_metrics = {
            "sn_total": 1,
            "tr_total": 3600,
            "st_total": 1,
            "lod_total": 50000,
            "dr_total": 0,
            "pc_total": 2000,
        }
        score = calculate_score(worst_metrics)
        assert score <= 0.5
