"""Tests for factory functions and data generation.

Verifies that:
- All factories generate valid test data
- IDs contain _TEST prefix for isolation
- Compatible layers actually have overlapping ranges
- Incompatible layers fail validation
"""

import pytest
from tests.factories import (
    TEST_PREFIX,
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
    make_compatible_four_layers,
    make_incompatible_four_layers,
    AnalyteFactory,
    BioRecognitionLayerFactory,
    ImmobilizationLayerFactory,
    MemristiveLayerFactory,
)


class TestFactoryPrefixes:
    """Test that all factories use _TEST prefix in IDs."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_analyte_factory_uses_test_prefix(self):
        """Analyte ID contains _TEST prefix."""
        AnalyteFactory.reset_counter()
        analyte = make_analyte()
        assert TEST_PREFIX in analyte["ta_id"]
        assert analyte["ta_id"].startswith("TA")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_bio_recognition_factory_uses_test_prefix(self):
        """BioRecognitionLayer ID contains _TEST prefix."""
        BioRecognitionLayerFactory.reset_counter()
        bio = make_bio_recognition_layer()
        assert TEST_PREFIX in bio["bre_id"]
        assert bio["bre_id"].startswith("BRE")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_immobilization_factory_uses_test_prefix(self):
        """ImmobilizationLayer ID contains _TEST prefix."""
        ImmobilizationLayerFactory.reset_counter()
        immob = make_immobilization_layer()
        assert TEST_PREFIX in immob["im_id"]
        assert immob["im_id"].startswith("IM")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_memristive_factory_uses_test_prefix(self):
        """MemristiveLayer ID contains _TEST prefix."""
        MemristiveLayerFactory.reset_counter()
        mem = make_memristive_layer()
        assert TEST_PREFIX in mem["mem_id"]
        assert mem["mem_id"].startswith("MEM")


class TestFactoryValidation:
    """Test that factory data is valid according to constraints."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_analyte_has_valid_ranges(self):
        """Analyte fields are within valid ranges."""
        analyte = make_analyte()
        assert 2.0 <= analyte["ph_min"] <= 10.0
        assert 2.0 <= analyte["ph_max"] <= 10.0
        assert analyte["ph_min"] <= analyte["ph_max"]
        assert 0 <= analyte["t_max"] <= 180
        assert 0 <= analyte["stability"] <= 365
        assert 0 <= analyte["half_life"] <= 8760
        assert 0 <= analyte["power_consumption"] <= 1000

    @pytest.mark.unit
    @pytest.mark.fast
    def test_bio_recognition_layer_has_valid_ranges(self):
        """BioRecognitionLayer fields are within valid ranges."""
        bio = make_bio_recognition_layer()
        assert 2.0 <= bio["ph_min"] <= 10.0
        assert 2.0 <= bio["ph_max"] <= 10.0
        assert bio["ph_min"] <= bio["ph_max"]
        assert 4 <= bio["t_min"] <= 120
        assert 4 <= bio["t_max"] <= 120
        assert bio["t_min"] <= bio["t_max"]
        assert 0.1 <= bio["dr_min"] <= 1000000000000.0
        assert 0.1 <= bio["dr_max"] <= 1000000000000.0
        assert bio["dr_min"] <= bio["dr_max"]
        assert 0 <= bio["sensitivity"] <= 20000
        assert 0 <= bio["reproducibility"] <= 100
        assert 0 <= bio["response_time"] <= 3600
        assert 0 <= bio["stability"] <= 365
        assert 0 <= bio["lod"] <= 50000
        assert 0 <= bio["durability"] <= 8760
        assert 0 <= bio["power_consumption"] <= 1000

    @pytest.mark.unit
    @pytest.mark.fast
    def test_immobilization_layer_has_valid_ranges(self):
        """ImmobilizationLayer fields are within valid ranges."""
        immob = make_immobilization_layer()
        assert 2.0 <= immob["ph_min"] <= 10.0
        assert 2.0 <= immob["ph_max"] <= 10.0
        assert immob["ph_min"] <= immob["ph_max"]
        assert 4 <= immob["t_min"] <= 120
        assert 4 <= immob["t_max"] <= 120
        assert immob["t_min"] <= immob["t_max"]
        assert 0 <= immob["young_modulus"] <= 1000
        assert immob["adhesion"] in ["слабая", "хорошая", "отличная"]
        assert immob["solubility"] in ["водорастворимый", "органический", "нерастворимый"]
        assert 0.0 <= immob["loss_coefficient"] <= 1.0
        assert 0 <= immob["reproducibility"] <= 100
        assert 0 <= immob["response_time"] <= 3600
        assert 0 <= immob["stability"] <= 365
        assert 0 <= immob["durability"] <= 8760
        assert 0 <= immob["power_consumption"] <= 1000

    @pytest.mark.unit
    @pytest.mark.fast
    def test_memristive_layer_has_valid_ranges(self):
        """MemristiveLayer fields are within valid ranges."""
        mem = make_memristive_layer()
        assert 2.0 <= mem["ph_min"] <= 10.0
        assert 2.0 <= mem["ph_max"] <= 10.0
        assert mem["ph_min"] <= mem["ph_max"]
        assert 5 <= mem["t_min"] <= 120
        assert 5 <= mem["t_max"] <= 120
        assert mem["t_min"] <= mem["t_max"]
        assert 0.0000001 <= mem["dr_min"] <= 100000000000.0
        assert 0.0000001 <= mem["dr_max"] <= 100000000000.0
        assert mem["dr_min"] <= mem["dr_max"]
        assert 0 <= mem["young_modulus"] <= 1000
        assert 0 <= mem["sensitivity"] <= 20000
        assert 0 <= mem["reproducibility"] <= 100
        assert 0 <= mem["response_time"] <= 3600
        assert 0 <= mem["stability"] <= 365
        assert 0 <= mem["lod"] <= 50000
        assert 0 <= mem["durability"] <= 8760
        assert 0 <= mem["power_consumption"] <= 1000


class TestCompatibleLayers:
    """Test make_compatible_four_layers function."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_compatible_layers_have_overlapping_ph(self):
        """pH ranges of compatible layers overlap."""
        analyte, bio, immob, mem = make_compatible_four_layers()

        # Extract pH ranges
        analyte_ph = (analyte["ph_min"], analyte["ph_max"])
        bio_ph = (bio["ph_min"], bio["ph_max"])
        immob_ph = (immob["ph_min"], immob["ph_max"])
        mem_ph = (mem["ph_min"], mem["ph_max"])

        # Check pairwise overlap: max(mins) <= min(maxs)
        assert max(analyte_ph[0], bio_ph[0], immob_ph[0], mem_ph[0]) <= min(
            analyte_ph[1], bio_ph[1], immob_ph[1], mem_ph[1]
        )

    @pytest.mark.unit
    @pytest.mark.fast
    def test_compatible_layers_have_overlapping_temperature(self):
        """Temperature ranges of compatible layers overlap."""
        analyte, bio, immob, mem = make_compatible_four_layers()

        # Analyte doesn't have t_min, only t_max
        analyte_t_max = analyte["t_max"]
        bio_t = (bio["t_min"], bio["t_max"])
        immob_t = (immob["t_min"], immob["t_max"])
        mem_t = (mem["t_min"], mem["t_max"])

        # Check overlap for layers with ranges
        assert max(bio_t[0], immob_t[0], mem_t[0]) <= min(bio_t[1], immob_t[1], mem_t[1])
        # And ensure analyte t_max is compatible
        assert analyte_t_max >= max(bio_t[0], immob_t[0], mem_t[0])

    @pytest.mark.unit
    @pytest.mark.fast
    def test_compatible_layers_have_close_young_modulus(self):
        """Young modulus of compatible layers is within 50 GPa."""
        analyte, bio, immob, mem = make_compatible_four_layers()

        immob_modulus = immob["young_modulus"]
        mem_modulus = mem["young_modulus"]

        modulus_diff = abs(immob_modulus - mem_modulus)
        assert modulus_diff <= 50  # Within 50 GPa tolerance


class TestIncompatibleLayers:
    """Test make_incompatible_four_layers function."""

    @pytest.mark.unit
    @pytest.mark.fast
    @pytest.mark.parametrize("reason", ["ph", "temperature", "mechanical"])
    def test_incompatible_layers_have_mismatched_ranges(self, reason: str):
        """Incompatible layers are actually incompatible."""
        analyte, bio, immob, mem = make_incompatible_four_layers(reason)

        if reason == "ph":
            # pH ranges don't overlap
            assert not (
                analyte["ph_min"] <= bio["ph_max"] and analyte["ph_max"] >= bio["ph_min"]
            )

        elif reason == "temperature":
            # Temperature ranges don't overlap
            assert not (
                analyte["t_max"] >= bio["t_min"]  # Simple check for analyte
            )

        else:  # mechanical
            # Young modulus difference > 50 GPa
            modulus_diff = abs(immob["young_modulus"] - mem["young_modulus"])
            assert modulus_diff > 50


class TestFactoryDeterminism:
    """Test that factories are deterministic."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_same_override_produces_same_data(self):
        """Same overrides produce identical data."""
        AnalyteFactory.reset_counter()
        analyte1 = make_analyte(ta_name="TestAnalyte", ph_min=5.0)

        AnalyteFactory.reset_counter()
        analyte2 = make_analyte(ta_name="TestAnalyte", ph_min=5.0)

        assert analyte1 == analyte2

    @pytest.mark.unit
    @pytest.mark.fast
    def test_compatible_layers_are_deterministic(self):
        """Compatible layers are deterministic across calls."""
        layers1 = make_compatible_four_layers()
        layers2 = make_compatible_four_layers()

        # Check that all 4 layers match
        for l1, l2 in zip(layers1, layers2):
            assert l1 == l2
