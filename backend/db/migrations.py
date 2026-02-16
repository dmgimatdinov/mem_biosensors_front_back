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
        # если колонка уже есть – ничего не делаем
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
    # ...

# Список всех миграций
ALL_MIGRATIONS = [
    migration_v1_add_created_at,
    migration_v2_add_updated_at,
]
