import sqlite3

import pytest

from db.migrations import migration_v3_add_reliability_fields, rollback_v3_remove_reliability_fields
from services.combination_synthesis import CombinationSynthesisService
from tests.factories import (
    make_compatible_four_layers,
)

pytestmark = pytest.mark.integration


def test_full_pipeline_with_reliability(tmp_db):
    analyte, bio, immob, mem = make_compatible_four_layers()

    bio["reliability_category"] = "low"
    bio["data_completeness"] = 0.60

    immob["reliability_category"] = "medium"
    immob["data_completeness"] = 0.70

    mem["reliability_category"] = "high"
    mem["data_completeness"] = 0.90

    tmp_db.insert_analyte(analyte)
    tmp_db.insert_bio_recognition_layer(bio)
    tmp_db.insert_immobilization_layer(immob)
    tmp_db.insert_memristive_layer(mem)

    service = CombinationSynthesisService(tmp_db)
    created = service.create_combination(analyte, bio, immob, mem)
    assert created is True

    combos = tmp_db.list_all_sensor_combinations()
    assert len(combos) == 1
    final_score = combos[0]["Score"]

    metrics = service._calculate_metrics(
        service._normalize_record(analyte, "analyte"),
        service._normalize_record(bio, "bio"),
        service._normalize_record(immob, "immob"),
        service._normalize_record(mem, "mem"),
    )
    raw_score = service._calculate_score(metrics)

    assert 0 <= final_score <= 10
    assert final_score < raw_score


def test_migration_rollback(tmp_path):
    db_path = tmp_path / "rollback.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE Analytes (TA_ID VARCHAR PRIMARY KEY, TA_Name VARCHAR NOT NULL);
        CREATE TABLE BioRecognitionLayers (BRE_ID VARCHAR PRIMARY KEY, BRE_Name VARCHAR NOT NULL);
        CREATE TABLE ImmobilizationLayers (IM_ID VARCHAR PRIMARY KEY, IM_Name VARCHAR NOT NULL);
        CREATE TABLE MemristiveLayers (MEM_ID VARCHAR PRIMARY KEY, MEM_Name VARCHAR NOT NULL);
        """
    )
    conn.commit()
    conn.close()

    migration_v3_add_reliability_fields(str(db_path))
    rollback_v3_remove_reliability_fields(str(db_path))

    conn = sqlite3.connect(str(db_path))
    for table in [
        "Analytes",
        "BioRecognitionLayers",
        "ImmobilizationLayers",
        "MemristiveLayers",
    ]:
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        assert "source_type" not in cols
        assert "source_doi" not in cols
        assert "source_date" not in cols
        assert "reliability_category" not in cols
        assert "data_completeness" not in cols
    conn.close()
