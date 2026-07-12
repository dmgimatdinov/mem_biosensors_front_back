import sqlite3

import pytest

from db.migrations import migration_v3_add_reliability_fields

pytestmark = pytest.mark.unit


def _create_legacy_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE Analytes (
            TA_ID VARCHAR PRIMARY KEY,
            TA_Name VARCHAR NOT NULL,
            PH_Min REAL,
            PH_Max REAL,
            T_Max REAL,
            ST REAL,
            HL REAL,
            PC REAL
        );

        CREATE TABLE BioRecognitionLayers (
            BRE_ID VARCHAR PRIMARY KEY,
            BRE_Name VARCHAR NOT NULL,
            PH_Min REAL,
            PH_Max REAL,
            T_Min REAL,
            T_Max REAL,
            SN REAL,
            DR_Min REAL,
            DR_Max REAL,
            RP REAL,
            TR REAL,
            ST REAL,
            LOD REAL,
            HL REAL,
            PC REAL
        );

        CREATE TABLE ImmobilizationLayers (
            IM_ID VARCHAR PRIMARY KEY,
            IM_Name VARCHAR NOT NULL,
            PH_Min REAL,
            PH_Max REAL,
            T_Min REAL,
            T_Max REAL,
            MP REAL,
            Adh VARCHAR,
            Sol VARCHAR,
            K_IM REAL,
            RP REAL,
            TR REAL,
            ST REAL,
            HL REAL,
            PC REAL
        );

        CREATE TABLE MemristiveLayers (
            MEM_ID VARCHAR PRIMARY KEY,
            MEM_Name VARCHAR NOT NULL,
            PH_Min REAL,
            PH_Max REAL,
            T_Min REAL,
            T_Max REAL,
            MP REAL,
            SN REAL,
            DR_Min REAL,
            DR_Max REAL,
            RP REAL,
            TR REAL,
            ST REAL,
            LOD REAL,
            HL REAL,
            PC REAL
        );
        """
    )


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def test_migration_applies_cleanly(tmp_path):
    db_path = tmp_path / "legacy_clean.db"
    conn = sqlite3.connect(str(db_path))
    _create_legacy_tables(conn)
    conn.commit()
    conn.close()

    migration_v3_add_reliability_fields(str(db_path))

    conn = sqlite3.connect(str(db_path))
    for table in [
        "Analytes",
        "BioRecognitionLayers",
        "ImmobilizationLayers",
        "MemristiveLayers",
    ]:
        columns = _column_names(conn, table)
        assert "source_type" in columns
        assert "source_doi" in columns
        assert "source_date" in columns
        assert "reliability_category" in columns
        assert "data_completeness" in columns
    conn.close()


def test_migration_preserves_existing_data(tmp_path):
    db_path = tmp_path / "legacy_data.db"
    conn = sqlite3.connect(str(db_path))
    _create_legacy_tables(conn)
    conn.execute(
        """
        INSERT INTO Analytes (TA_ID, TA_Name, PH_Min, PH_Max, T_Max, ST, HL, PC)
        VALUES ('TA_TEST001', 'Glucose', 4.0, 8.0, 37.0, 90.0, 500.0, 20.0)
        """
    )
    conn.commit()
    conn.close()

    migration_v3_add_reliability_fields(str(db_path))

    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        """
        SELECT TA_ID, TA_Name, reliability_category, data_completeness
        FROM Analytes
        WHERE TA_ID='TA_TEST001'
        """
    ).fetchone()
    conn.close()

    assert row[0] == "TA_TEST001"
    assert row[1] == "Glucose"
    assert row[2] == "medium"
    assert row[3] == pytest.approx(0.5)
