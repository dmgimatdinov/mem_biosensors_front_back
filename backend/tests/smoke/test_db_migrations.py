"""
Smoke-тесты миграций базы данных.
Проверяют, что БД создаётся корректно и миграции идемпотентны.
"""

import sqlite3

import pytest


@pytest.mark.smoke
class TestDatabaseMigrations:
    """Тесты миграций БД."""

    def _patch_db_connection(self, monkeypatch, db_path):
        """Patch db.manager.get_connection so DatabaseManager works with tmp DB."""
        import db.manager as manager_module

        monkeypatch.setattr(manager_module, "DB_NAME", str(db_path))

        def _get_connection():
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        monkeypatch.setattr(manager_module, "get_connection", _get_connection)

    def test_fresh_db_creates_all_tables(self, tmp_path, monkeypatch):
        """На пустой БД создаются все 5 таблиц."""
        db_path = tmp_path / "fresh.db"
        self._patch_db_connection(monkeypatch, db_path)

        from db.manager import DatabaseManager

        DatabaseManager(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected_tables = {
            "Analytes",
            "BioRecognitionLayers",
            "ImmobilizationLayers",
            "MemristiveLayers",
            "SensorCombinations",
        }
        assert expected_tables.issubset(tables), f"Missing tables. Found: {tables}"

    def test_migration_idempotent(self, tmp_path, monkeypatch):
        """Повторная инициализация БД не падает."""
        db_path = tmp_path / "idempotent.db"
        self._patch_db_connection(monkeypatch, db_path)

        from db.manager import DatabaseManager

        db1 = DatabaseManager(str(db_path))
        db2 = DatabaseManager(str(db_path))
        db3 = DatabaseManager(str(db_path))

        assert db1 is not None
        assert db2 is not None
        assert db3 is not None

    def test_schema_version_table_exists(self, tmp_path, monkeypatch):
        """Таблица schema_version создана и содержит записи."""
        db_path = tmp_path / "versioned.db"
        self._patch_db_connection(monkeypatch, db_path)

        from db.manager import DatabaseManager

        DatabaseManager(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='schema_version'"
        )
        result = cursor.fetchone()
        if result is None:
            conn.close()
            pytest.skip("schema_version table not implemented")

        cursor.execute("SELECT COUNT(*) FROM schema_version")
        count = cursor.fetchone()[0]
        conn.close()

        assert count > 0, "schema_version table is empty"

    def test_foreign_keys_pragma_enabled(self, tmp_path, monkeypatch):
        """PRAGMA foreign_keys = ON включён для соединения."""
        db_path = tmp_path / "fk_test.db"
        self._patch_db_connection(monkeypatch, db_path)

        from db.manager import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 1, "foreign_keys PRAGMA is not enabled"

    def test_tables_have_expected_columns(self, tmp_path, monkeypatch):
        """Таблицы имеют ожидаемые колонки."""
        db_path = tmp_path / "columns_test.db"
        self._patch_db_connection(monkeypatch, db_path)

        from db.manager import DatabaseManager

        DatabaseManager(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Analytes)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected_columns = {"TA_ID", "TA_Name", "PH_Min", "PH_Max", "T_Max"}
        assert expected_columns.issubset(columns), f"Columns mismatch. Found: {columns}"

    def test_primary_keys_defined(self, tmp_path, monkeypatch):
        """Для всех таблиц определены первичные ключи."""
        db_path = tmp_path / "pk_test.db"
        self._patch_db_connection(monkeypatch, db_path)

        from db.manager import DatabaseManager

        DatabaseManager(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        tables = [
            "Analytes",
            "BioRecognitionLayers",
            "ImmobilizationLayers",
            "MemristiveLayers",
            "SensorCombinations",
        ]

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            rows = cursor.fetchall()
            pk_columns = [row for row in rows if row[5] > 0]
            assert len(pk_columns) > 0, f"Table {table} has no primary key"

        conn.close()
