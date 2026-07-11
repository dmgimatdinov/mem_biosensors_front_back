import pytest

from services.metrics_calculator import (
    calculate_sn_total,
    calculate_tr_total,
    calculate_st_total,
    calculate_lod_total,
    calculate_dr_total,
    calculate_pc_total,
)
from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
)

pytestmark = pytest.mark.unit


class TestMetricsCalculator:
    def test_sn_total_formula(self):
        """SN_total = SN_bio × SN_mem × K_IM."""
        bio = make_bio_recognition_layer(sensitivity=1000)
        im = make_immobilization_layer(loss_coefficient=0.5)
        mem = make_memristive_layer(sensitivity=200)

        sn_total = calculate_sn_total(bio, im, mem)
        expected = 1000 * 200 * 0.5
        assert sn_total == expected

    def test_tr_total_formula(self):
        """TR_total = TR_bio + TR_im + TR_mem."""
        bio = make_bio_recognition_layer(response_time=30)
        im = make_immobilization_layer(response_time=60)
        mem = make_memristive_layer(response_time=10)

        tr_total = calculate_tr_total(bio, im, mem)
        assert tr_total == 100

    def test_st_total_is_minimum(self):
        """ST_total = min(ST_bio, ST_im, ST_mem)."""
        bio = make_bio_recognition_layer(stability=90)
        im = make_immobilization_layer(stability=120)
        mem = make_memristive_layer(stability=60)

        st_total = calculate_st_total(bio, im, mem)
        assert st_total == 60

    def test_lod_total_is_maximum(self):
        """LOD_total = max(LOD_bio, LOD_mem)."""
        bio = make_bio_recognition_layer(lod=100)
        mem = make_memristive_layer(lod=50)

        lod_total = calculate_lod_total(bio, mem)
        assert lod_total == 100

    def test_dr_total_is_intersection(self):
        """DR_total = пересечение диапазонов."""
        bio = make_bio_recognition_layer(dr_min=0.1, dr_max=1000.0)
        mem = make_memristive_layer(dr_min=0.5, dr_max=500.0)

        dr_total = calculate_dr_total(bio, mem)
        expected = max(0, min(1000.0, 500.0) - max(0.1, 0.5))
        assert abs(dr_total - expected) < 1e-9

    def test_pc_total_is_sum(self):
        """PC_total = сумма энергопотреблений."""
        analyte = make_analyte(power_consumption=500)
        bio = make_bio_recognition_layer(power_consumption=200)
        im = make_immobilization_layer(power_consumption=100)
        mem = make_memristive_layer(power_consumption=300)

        pc_total = calculate_pc_total(analyte, bio, im, mem)
        assert pc_total == 1100
