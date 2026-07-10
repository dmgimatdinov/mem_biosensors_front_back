"""Factories for generating test data with deterministic values.

All test data uses _TEST prefix for IDs to ensure isolation and determinism.
"""

from typing import Dict, Any, List, Literal
from faker import Faker
import random

fake = Faker()
random.seed(42)  # Deterministic randomness
Faker.seed(42)

TEST_PREFIX = "_TEST"


class AnalyteFactory:
    """Factory for generating test Analytes."""

    _counter = 0

    @classmethod
    def reset_counter(cls) -> None:
        cls._counter = 0

    @classmethod
    def create(cls, **overrides: Any) -> Dict[str, Any]:
        """Generate a valid Analyte with test prefix.

        Args:
            **overrides: Optional field overrides

        Returns:
            Dict with Analyte data
        """
        cls._counter += 1
        defaults = {
            "ta_id": f"TA{TEST_PREFIX}{cls._counter:03d}",
            "ta_name": f"Test Analyte {cls._counter}",
            "ph_min": 3.0,
            "ph_max": 8.0,
            "t_max": 37,
            "stability": 30,
            "half_life": 720,
            "power_consumption": 100,
        }
        defaults.update(overrides)
        return defaults


class BioRecognitionLayerFactory:
    """Factory for generating test BioRecognitionLayers."""

    _counter = 0

    @classmethod
    def reset_counter(cls) -> None:
        cls._counter = 0

    @classmethod
    def create(cls, **overrides: Any) -> Dict[str, Any]:
        """Generate a valid BioRecognitionLayer with test prefix.

        Args:
            **overrides: Optional field overrides

        Returns:
            Dict with BioRecognitionLayer data
        """
        cls._counter += 1
        defaults = {
            "bre_id": f"BRE{TEST_PREFIX}{cls._counter:03d}",
            "bre_name": f"Test Bio Layer {cls._counter}",
            "ph_min": 3.0,
            "ph_max": 8.0,
            "t_min": 10,
            "t_max": 40,
            "sensitivity": 500,
            "reproducibility": 95,
            "response_time": 120,
            "stability": 60,
            "lod": 1000,
            "durability": 2000,
            "power_consumption": 50,
            "dr_min": 1.0,
            "dr_max": 1000000.0,
        }
        defaults.update(overrides)
        return defaults


class ImmobilizationLayerFactory:
    """Factory for generating test ImmobilizationLayers."""

    _counter = 0

    @classmethod
    def reset_counter(cls) -> None:
        cls._counter = 0

    @classmethod
    def create(cls, **overrides: Any) -> Dict[str, Any]:
        """Generate a valid ImmobilizationLayer with test prefix.

        Args:
            **overrides: Optional field overrides

        Returns:
            Dict with ImmobilizationLayer data
        """
        cls._counter += 1
        defaults = {
            "im_id": f"IM{TEST_PREFIX}{cls._counter:03d}",
            "im_name": f"Test Immobilization Layer {cls._counter}",
            "ph_min": 3.0,
            "ph_max": 8.0,
            "t_min": 10,
            "t_max": 40,
            "young_modulus": 50,
            "adhesion": "хорошая",
            "solubility": "водорастворимый",
            "loss_coefficient": 0.5,
            "reproducibility": 92,
            "response_time": 100,
            "stability": 60,
            "durability": 2000,
            "power_consumption": 40,
        }
        defaults.update(overrides)
        return defaults


class MemristiveLayerFactory:
    """Factory for generating test MemristiveLayers."""

    _counter = 0

    @classmethod
    def reset_counter(cls) -> None:
        cls._counter = 0

    @classmethod
    def create(cls, **overrides: Any) -> Dict[str, Any]:
        """Generate a valid MemristiveLayer with test prefix.

        Args:
            **overrides: Optional field overrides

        Returns:
            Dict with MemristiveLayer data
        """
        cls._counter += 1
        defaults = {
            "mem_id": f"MEM{TEST_PREFIX}{cls._counter:03d}",
            "mem_name": f"Test Memristive Layer {cls._counter}",
            "ph_min": 3.0,
            "ph_max": 8.0,
            "t_min": 10,
            "t_max": 40,
            "young_modulus": 55,
            "sensitivity": 450,
            "reproducibility": 94,
            "response_time": 110,
            "stability": 60,
            "lod": 1100,
            "durability": 2000,
            "power_consumption": 45,
            "dr_min": 1.0,
            "dr_max": 1000000.0,
        }
        defaults.update(overrides)
        return defaults


def make_analyte(**overrides: Any) -> Dict[str, Any]:
    """Convenience function to create a test Analyte."""
    return AnalyteFactory.create(**overrides)


def make_bio_recognition_layer(**overrides: Any) -> Dict[str, Any]:
    """Convenience function to create a test BioRecognitionLayer."""
    return BioRecognitionLayerFactory.create(**overrides)


def make_immobilization_layer(**overrides: Any) -> Dict[str, Any]:
    """Convenience function to create a test ImmobilizationLayer."""
    return ImmobilizationLayerFactory.create(**overrides)


def make_memristive_layer(**overrides: Any) -> Dict[str, Any]:
    """Convenience function to create a test MemristiveLayer."""
    return MemristiveLayerFactory.create(**overrides)


def make_compatible_four_layers() -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Create 4 compatible layers with matching pH/temperature ranges.

    Returns:
        Tuple of (analyte, bio_layer, immobilization_layer, memristive_layer)

    Notes:
        - pH ranges overlap at 3.0-8.0
        - Temperature ranges overlap at 10-40°C
        - Young modulus difference ≤ 0.5 GPa (50 vs 55)
    """
    # Reset counters for predictable IDs
    AnalyteFactory.reset_counter()
    BioRecognitionLayerFactory.reset_counter()
    ImmobilizationLayerFactory.reset_counter()
    MemristiveLayerFactory.reset_counter()

    analyte = make_analyte(
        ph_min=3.0,
        ph_max=8.0,
        t_max=40,
    )

    bio_layer = make_bio_recognition_layer(
        ph_min=3.0,
        ph_max=8.0,
        t_min=10,
        t_max=40,
    )

    immobilization_layer = make_immobilization_layer(
        ph_min=3.0,
        ph_max=8.0,
        t_min=10,
        t_max=40,
        young_modulus=50,
    )

    memristive_layer = make_memristive_layer(
        ph_min=3.0,
        ph_max=8.0,
        t_min=10,
        t_max=40,
        young_modulus=55,  # Difference = 5, within 50 GPa tolerance
    )

    return analyte, bio_layer, immobilization_layer, memristive_layer


def make_incompatible_four_layers(
    reason: Literal["ph", "temperature", "mechanical"] = "ph"
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Create 4 incompatible layers for testing validation.

    Args:
        reason: Type of incompatibility:
            - "ph": pH ranges don't overlap
            - "temperature": Temperature ranges don't overlap
            - "mechanical": Young modulus difference > 50 GPa

    Returns:
        Tuple of (analyte, bio_layer, immobilization_layer, memristive_layer)
    """
    # Reset counters for predictable IDs
    AnalyteFactory.reset_counter()
    BioRecognitionLayerFactory.reset_counter()
    ImmobilizationLayerFactory.reset_counter()
    MemristiveLayerFactory.reset_counter()

    if reason == "ph":
        analyte = make_analyte(ph_min=2.0, ph_max=3.0)  # pH 2-3
        bio_layer = make_bio_recognition_layer(ph_min=8.0, ph_max=9.0)  # pH 8-9 (no overlap)
        immobilization_layer = make_immobilization_layer(ph_min=2.0, ph_max=3.0)
        memristive_layer = make_memristive_layer(ph_min=2.0, ph_max=3.0)

    elif reason == "temperature":
        analyte = make_analyte(t_max=20)  # Max 20°C
        bio_layer = make_bio_recognition_layer(t_min=40, t_max=80)  # 40-80°C (no overlap)
        immobilization_layer = make_immobilization_layer(t_min=40, t_max=80)
        memristive_layer = make_memristive_layer(t_min=40, t_max=80)

    else:  # mechanical
        analyte = make_analyte()
        bio_layer = make_bio_recognition_layer()
        immobilization_layer = make_immobilization_layer(young_modulus=10)  # 10 GPa
        memristive_layer = make_memristive_layer(young_modulus=100)  # 100 GPa (diff = 90 > 50)

    return analyte, bio_layer, immobilization_layer, memristive_layer
