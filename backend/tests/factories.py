# backend/tests/factories.py
"""Factory functions for creating test data for all entity types."""

from typing import Dict, Any


def make_analyte(**overrides) -> Dict[str, Any]:
    """Factory for creating Analyte test data."""
    defaults = {
        "ta_id": "TA_TEST_001",
        "ta_name": "Glucose",
        "ph_min": 5.0,
        "ph_max": 8.0,
        "t_max": 50,
        "stability": 30,
        "half_life": 1000,
        "power_consumption": 100,
    }
    defaults.update(overrides)
    return defaults


def make_bio_recognition_layer(**overrides) -> Dict[str, Any]:
    """Factory for creating BioRecognitionLayer test data."""
    defaults = {
        "bre_id": "BRE_TEST_001",
        "bre_name": "Antibody",
        "ph_min": 5.0,
        "ph_max": 8.0,
        "t_min": 20,
        "t_max": 40,
        "dr_min": 0.1,
        "dr_max": 10.0,
        "sensitivity": 1000,
        "reproducibility": 90,
        "response_time": 30,
        "stability": 180,
        "lod": 1,
        "durability": 2000,
        "power_consumption": 200,
    }
    defaults.update(overrides)
    return defaults


def make_immobilization_layer(**overrides) -> Dict[str, Any]:
    """Factory for creating ImmobilizationLayer test data."""
    defaults = {
        "im_id": "IM_TEST_001",
        "im_name": "Polymer",
        "ph_min": 5.0,
        "ph_max": 8.0,
        "t_min": 20,
        "t_max": 50,
        "young_modulus": 50,
        "adhesion": "хорошая",
        "solubility": "водорастворимый",
        "loss_coefficient": 0.1,
        "reproducibility": 90,
        "response_time": 30,
        "stability": 180,
        "durability": 2000,
        "power_consumption": 200,
    }
    defaults.update(overrides)
    return defaults


def make_memristive_layer(**overrides) -> Dict[str, Any]:
    """Factory for creating MemristiveLayer test data."""
    defaults = {
        "mem_id": "MEM_TEST_001",
        "mem_name": "Memristor",
        "ph_min": 5.0,
        "ph_max": 8.0,
        "t_min": 20,
        "t_max": 50,
        "dr_min": 0.1,
        "dr_max": 100.0,
        "young_modulus": 40,
        "sensitivity": 1500,
        "reproducibility": 95,
        "response_time": 20,
        "stability": 200,
        "lod": 1,
        "durability": 3000,
        "power_consumption": 150,
    }
    defaults.update(overrides)
    return defaults
