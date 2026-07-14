import sqlite3
import threading

import pytest

from db.migrations import ALL_MIGRATIONS, MigrationManager


@pytest.mark.smoke
def test_parallel_migrations_no_race_condition(tmp_path):
    """Параллельный запуск миграций на одной БД не вызывает IntegrityError."""
    db_path = tmp_path / "parallel.db"
    errors = []

    def run_migration():
        try:
            migrator = MigrationManager(str(db_path))
            migrator.migrate(ALL_MIGRATIONS)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=run_migration) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Parallel migrations failed: {errors}"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schema_version")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == len(ALL_MIGRATIONS)
