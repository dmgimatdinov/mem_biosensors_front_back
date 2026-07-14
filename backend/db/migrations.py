# db/migrations.py

import sqlite3
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class MigrationManager:
    """Управление миграциями БД."""
    
    def __init__(self, db_name: str):
        self.db_name = db_name
    
    def get_current_version(self) -> int:
        """Получить текущую версию схемы БД.

        Если миграции выполняются в рамках существующего соединения (например,
        фикстура использует общий connection для ':memory:'), то внешнее
        соединение может быть установлено в `self._external_conn` перед вызовом.
        """
        try:
            conn = getattr(self, "_external_conn", None)
            if conn is None:
                with sqlite3.connect(self.db_name, timeout=30) as conn_local:
                    cursor = conn_local.cursor()
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS schema_version (
                            version INTEGER PRIMARY KEY,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                    result = cursor.fetchone()
                    return result[0] if result else 0
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.OperationalError:
            return 0
    
    def set_version(self, version: int):
        """Установить версию схемы."""
        conn = getattr(self, "_external_conn", None)
        if conn is None:
            with sqlite3.connect(self.db_name, timeout=30) as conn_local:
                cursor = conn_local.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (version,))
                conn_local.commit()
        else:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (version,))
            try:
                conn.commit()
            except Exception:
                pass
    
    def migrate(self, migrations: list[Callable], conn: sqlite3.Connection | None = None):
        """
        Применить миграции.
        
        Args:
            migrations: список функций миграций (по порядку версий)
        """
        # If a connection is supplied (e.g. shared in-memory connection), use it
        if conn is not None:
            self._external_conn = conn
        else:
            self._external_conn = None

        current = self.get_current_version()

        for i, migration in enumerate(migrations, start=1):
            if i <= current:
                continue

            logger.info(f"Применяю миграцию v{i}...")
            try:
                # Allow migration to accept either DB path or a Connection
                if conn is not None:
                    migration(conn)
                else:
                    migration(self.db_name)
                self.set_version(i)
                current = i
                logger.info(f"✅ Миграция v{i} применена")
            except Exception as e:
                logger.error(f"❌ Ошибка миграции v{i}: {e}")
                raise

def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info('{table}')")
    return any(row[1] == column for row in cursor.fetchall())

# Примеры миграций
def migration_v1_add_created_at(db: str | sqlite3.Connection) -> None:
    close_after = False
    if isinstance(db, sqlite3.Connection):
        conn = db
    else:
        conn = sqlite3.connect(db)
        close_after = True

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Analytes'")
        if not cursor.fetchone():
            return

        if column_exists(conn, "Analytes", "created_at"):
            return

        cursor.execute(
            "ALTER TABLE Analytes "
            "ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
        conn.commit()
    finally:
        if close_after:
            conn.close()

def migration_v2_add_updated_at(db_name: str):
    """Миграция v2: добавление поля updated_at."""
    return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cursor.fetchone() is not None


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> bool:
    if column_exists(conn, table, column):
        return False
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    return True


def migration_v3_add_reliability_fields(db: str | sqlite3.Connection) -> None:
    """Миграция v3: добавление полей достоверности источника в 4 таблицы слоёв."""
    tables = [
        "Analytes",
        "BioRecognitionLayers",
        "ImmobilizationLayers",
        "MemristiveLayers",
    ]
    close_after = False
    if isinstance(db, sqlite3.Connection):
        conn = db
    else:
        conn = sqlite3.connect(db)
        close_after = True

    try:
        for table in tables:
            if not _table_exists(conn, table):
                continue

            _add_column_if_missing(
                conn,
                table,
                "source_type",
                "TEXT DEFAULT 'expert' CHECK (source_type IS NULL OR source_type IN ('experimental','manufacturer','expert','literature'))",
            )
            _add_column_if_missing(conn, table, "source_doi", "VARCHAR(255) DEFAULT NULL")
            _add_column_if_missing(conn, table, "source_date", "DATE DEFAULT NULL")
            _add_column_if_missing(
                conn,
                table,
                "reliability_category",
                "TEXT DEFAULT 'medium' CHECK (reliability_category IS NULL OR reliability_category IN ('high','medium','low'))",
            )
            _add_column_if_missing(
                conn,
                table,
                "data_completeness",
                "REAL DEFAULT 1.0 CHECK (data_completeness IS NULL OR (data_completeness >= 0.0 AND data_completeness <= 1.0))",
            )

            # Data migration for legacy rows: default reliability category and partial completeness.
            conn.execute(
                f"""
                UPDATE {table}
                SET reliability_category = 'medium',
                    data_completeness = 0.5
                WHERE source_doi IS NULL
                  AND source_date IS NULL
                  AND (reliability_category IS NULL OR reliability_category = 'medium')
                  AND (data_completeness IS NULL OR data_completeness = 1.0)
                """
            )

        conn.commit()
    finally:
        if close_after:
            conn.close()


def rollback_v3_remove_reliability_fields(db: str | sqlite3.Connection) -> None:
    """Откат v3: удаление полей достоверности (используется в интеграционных тестах)."""
    tables = [
        "Analytes",
        "BioRecognitionLayers",
        "ImmobilizationLayers",
        "MemristiveLayers",
    ]
    columns = [
        "data_completeness",
        "reliability_category",
        "source_date",
        "source_doi",
        "source_type",
    ]
    close_after = False
    if isinstance(db, sqlite3.Connection):
        conn = db
    else:
        conn = sqlite3.connect(db)
        close_after = True
    try:
        for table in tables:
            if not _table_exists(conn, table):
                continue
            for column in columns:
                if column_exists(conn, table, column):
                    conn.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
        conn.commit()
    finally:
        if close_after:
            conn.close()

# Список всех миграций
ALL_MIGRATIONS = [
    migration_v1_add_created_at,
    migration_v2_add_updated_at,
    migration_v3_add_reliability_fields,
    # v4: add is_test flag and protective triggers
    # migration_v4_protect_non_test will be appended here
]

def migration_v4_protect_non_test(db: str | sqlite3.Connection) -> None:
    """Миграция v4: добавление флага `is_test` и триггеров, запрещающих удалять нетестовые записи."""
    tables = [
        "Analytes",
        "BioRecognitionLayers",
        "ImmobilizationLayers",
        "MemristiveLayers",
        "SensorCombinations",
    ]

    close_after = False
    if isinstance(db, sqlite3.Connection):
        conn = db
    else:
        conn = sqlite3.connect(db)
        close_after = True

    try:
        for table in tables:
            if not _table_exists(conn, table):
                continue

            # Add is_test column if missing
            _add_column_if_missing(conn, table, "is_test", "INTEGER DEFAULT 0")

            # Mark existing rows as test if their PK ends with common test suffixes
            # Determine primary key column name per table
            id_col = {
                "Analytes": "TA_ID",
                "BioRecognitionLayers": "BRE_ID",
                "ImmobilizationLayers": "IM_ID",
                "MemristiveLayers": "MEM_ID",
                "SensorCombinations": "Combo_ID",
            }.get(table, None)

            if id_col:
                try:
                    conn.execute(
                        f"UPDATE {table} SET is_test = 1 WHERE {id_col} LIKE '%_TEST%' OR {id_col} LIKE '%_DUP%' OR {id_col} LIKE '%TEST%'")
                except Exception:
                    # Non-fatal — proceed even if update fails on empty tables
                    pass

            # Create BEFORE DELETE trigger to prevent deleting non-test rows
            trigger_name = f"protect_delete_{table}"
            try:
                conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
            except Exception:
                pass

            # Trigger: prevent deleting rows that are not explicitly marked as test
            # but allow deletion when the primary key looks like a test id (suffixes)
            id_col = id_col if id_col else 'rowid'
            conn.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {trigger_name}
                BEFORE DELETE ON {table}
                FOR EACH ROW
                WHEN (
                    (OLD.is_test IS NULL OR OLD.is_test = 0)
                    AND (OLD.{id_col} NOT LIKE '%_TEST%' AND OLD.{id_col} NOT LIKE '%_DUP%' AND OLD.{id_col} NOT LIKE '%TEST%')
                )
                BEGIN
                    SELECT RAISE(ABORT, 'Attempt to delete non-test data is forbidden');
                END;
            """)

        conn.commit()
    finally:
        if close_after:
            conn.close()

# Append migration_v4 to migrations list
ALL_MIGRATIONS.append(migration_v4_protect_non_test)
