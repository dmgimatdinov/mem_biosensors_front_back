import sqlite3

import pytest

from db.migrations import ALL_MIGRATIONS, MigrationManager


@pytest.mark.smoke
def test_migration_idempotent_on_same_db(tmp_path):
    """Повторный вызов migrate() на одной БД не падает."""
    db_path = tmp_path / "idempotent.db"

    migrator = MigrationManager(str(db_path))
    migrator.migrate(ALL_MIGRATIONS)

    migrator2 = MigrationManager(str(db_path))
    migrator2.migrate(ALL_MIGRATIONS)

    migrator3 = MigrationManager(str(db_path))
    migrator3.migrate(ALL_MIGRATIONS)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schema_version")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == len(ALL_MIGRATIONS)
