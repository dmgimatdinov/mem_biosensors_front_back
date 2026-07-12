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
        """Получить текущую версию схемы БД."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.OperationalError:
            # Таблица schema_version не существует
            return 0
    
    def set_version(self, version: int):
        """Установить версию схемы."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()
    
    def migrate(self, migrations: list[Callable]):
        """
        Применить миграции.
        
        Args:
            migrations: список функций миграций (по порядку версий)
        """
        current = self.get_current_version()
        
        for i, migration in enumerate(migrations, start=1):
            if i <= current:
                continue
            
            logger.info(f"Применяю миграцию v{i}...")
            try:
                migration(self.db_name)
                self.set_version(i)
                logger.info(f"✅ Миграция v{i} применена")
            except Exception as e:
                logger.error(f"❌ Ошибка миграции v{i}: {e}")
                raise

def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info('{table}')")
    return any(row[1] == column for row in cursor.fetchall())

# Примеры миграций
def migration_v1_add_created_at(db_name: str) -> None:
    conn = sqlite3.connect(db_name)
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


def migration_v3_add_reliability_fields(db_name: str) -> None:
    """Миграция v3: добавление полей достоверности источника в 4 таблицы слоёв."""
    tables = [
        "Analytes",
        "BioRecognitionLayers",
        "ImmobilizationLayers",
        "MemristiveLayers",
    ]
    conn = sqlite3.connect(db_name)
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
        conn.close()


def rollback_v3_remove_reliability_fields(db_name: str) -> None:
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
    conn = sqlite3.connect(db_name)
    try:
        for table in tables:
            if not _table_exists(conn, table):
                continue
            for column in columns:
                if column_exists(conn, table, column):
                    conn.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
        conn.commit()
    finally:
        conn.close()

# Список всех миграций
ALL_MIGRATIONS = [
    migration_v1_add_created_at,
    migration_v2_add_updated_at,
    migration_v3_add_reliability_fields,
]
