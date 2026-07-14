# db/manager.py
import sqlite3
import os
import shutil
from enum import Enum
from typing import Dict, Any, List
import logging
from functools import lru_cache

from db.exceptions import DatabaseConnectionError, DatabaseIntegrityError
from db.migrations import MigrationManager, ALL_MIGRATIONS

from services.biosensor_service import DatabaseAdapter

DB_NAME = os.getenv("DATABASE_PATH", "memristive_biosensor.db")

logger = logging.getLogger(__name__)


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

class TableConfig(Enum):
    """Конфигурация таблиц и их полей"""
    ANALYTES = {
        "table": "Analytes",
        "id_col": "TA_ID",
        "display_col": "TA_Name",
        "select_cols": ["TA_ID", "TA_Name", "PH_Min", "PH_Max", "T_Max", "ST"],
        "all_cols": ["TA_ID", "TA_Name", "PH_Min", "PH_Max", "T_Max", "ST", "HL", "PC"],
        "entity_name": "аналит",
        "entity_name_plural": "аналиты",
    }
    BIO_RECOGNITION = {
        "table": "BioRecognitionLayers",
        "id_col": "BRE_ID",
        "display_col": "BRE_Name",
        "select_cols": ["BRE_ID", "BRE_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "SN"],
        "all_cols": ["BRE_ID", "BRE_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "SN", "DR_Min", "DR_Max", "RP", "TR", "ST", "LOD", "HL", "PC"],
        "entity_name": "биослой",
        "entity_name_plural": "биослои",
    }
    IMMOBILIZATION = {
        "table": "ImmobilizationLayers",
        "id_col": "IM_ID",
        "display_col": "IM_Name",
        "select_cols": ["IM_ID", "IM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "MP"],
        "all_cols": ["IM_ID", "IM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "MP", "Adh", "Sol", "K_IM", "RP", "TR", "ST", "HL", "PC"],
        "entity_name": "иммобилизационный слой",
        "entity_name_plural": "иммобилизационные слои",
    }
    MEMRISTIVE = {
        "table": "MemristiveLayers",
        "id_col": "MEM_ID",
        "display_col": "MEM_Name",
        "select_cols": ["MEM_ID", "MEM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "SN"],
        "all_cols": ["MEM_ID", "MEM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "MP", "SN", "DR_Min", "DR_Max", "RP", "TR", "ST", "LOD", "HL", "PC"],
        "entity_name": "мемристивный слой",
        "entity_name_plural": "мемристивные слои",
    }
    SENSOR_COMBINATIONS = {
        "table": "SensorCombinations",
        "id_col": "Combo_ID",
        "display_col": "Combo_ID",
        "select_cols": ["Combo_ID", "TA_ID", "BRE_ID", "IM_ID", "MEM_ID", "Score"],
        "all_cols": ["Combo_ID", "TA_ID", "BRE_ID", "IM_ID", "MEM_ID", "SN_total", "TR_total", "ST_total", "RP_total", "LOD_total", "DR_total", "HL_total", "PC_total", "Score"],
        "entity_name": "комбинация сенсора",
        "entity_name_plural": "комбинации сенсоров",
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def __getitem__(self, key: str) -> Any:
        return self.config[key]

class DatabaseManager(DatabaseAdapter):
    """Слой работы с БД (без Streamlit)."""

    def _resolve_value(self, data: Dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data and data[key] is not None:
                return data[key]
        return None

    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.logger = logger
        # Если есть бэкап и основная БД пуста/потеряла данные — восстановим из бэкапа
        try:
            backup_path = f"{db_name}.backup"
            if os.path.exists(backup_path):
                need_restore = False
                # Если база не существует — восстановим
                if not os.path.exists(db_name):
                    need_restore = True
                else:
                    try:
                        with sqlite3.connect(db_name) as conn_main, sqlite3.connect(backup_path) as conn_bak:
                            cursor_main = conn_main.cursor()
                            cursor_bak = conn_bak.cursor()
                            # Проверяем суммарное количество строк в ключевых таблицах
                            tables = ["Analytes", "BioRecognitionLayers", "ImmobilizationLayers", "MemristiveLayers"]
                            main_count = 0
                            bak_count = 0
                            for t in tables:
                                try:
                                    cursor_main.execute(f"SELECT COUNT(1) FROM {t}")
                                    main_count += cursor_main.fetchone()[0]
                                except sqlite3.Error:
                                    # Таблица отсутствует или ошибка — считаем как 0
                                    pass
                                try:
                                    cursor_bak.execute(f"SELECT COUNT(1) FROM {t}")
                                    bak_count += cursor_bak.fetchone()[0]
                                except sqlite3.Error:
                                    pass

                            if bak_count > 0 and main_count == 0:
                                need_restore = True
                    except sqlite3.Error:
                        # Если не удалось прочитать, не восстанавливаем автоматически
                        need_restore = False

                if need_restore:
                    try:
                        shutil.copy2(backup_path, db_name)
                        self.logger.info(f"БД восстановлена из бэкапа: {backup_path} -> {db_name}")
                    except Exception as e:
                        self.logger.error(f"Не удалось восстановить БД из бэкапа: {e}")
        except Exception:
            # Не критично, продолжаем — мигратор сам создаст таблицы
            pass

        # Создать текущую схему для свежей БД, затем применить миграции к существующей схеме.
        try:
            self.create_tables()
        except sqlite3.Error as e:
            self.logger.critical(f"Не удалось инициализировать БД: {e}")
            raise DatabaseConnectionError(f"Ошибка подключения к {db_name}") from e

        migrator = MigrationManager(db_name)
        try:
            migrator.migrate(ALL_MIGRATIONS, conn=get_connection())
        except Exception:
            # Fallback to path-based migration if connection-based fails
            migrator.migrate(ALL_MIGRATIONS)

    def create_tables(self) -> None:
        """Создание таблиц базы данных, если они не существуют."""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS Analytes (
                TA_ID VARCHAR PRIMARY KEY,
                TA_Name VARCHAR NOT NULL,
                PH_Min REAL,
                PH_Max REAL,
                T_Max REAL,
                ST REAL,
                HL REAL,
                PC REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_type TEXT DEFAULT 'expert' CHECK (source_type IS NULL OR source_type IN ('experimental','manufacturer','expert','literature')),
                source_doi VARCHAR(255) DEFAULT NULL,
                source_date DATE DEFAULT NULL,
                reliability_category TEXT DEFAULT 'medium' CHECK (reliability_category IS NULL OR reliability_category IN ('high','medium','low')),
                data_completeness REAL DEFAULT 1.0 CHECK (data_completeness IS NULL OR (data_completeness >= 0.0 AND data_completeness <= 1.0))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS BioRecognitionLayers (
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
                PC REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_type TEXT DEFAULT 'expert' CHECK (source_type IS NULL OR source_type IN ('experimental','manufacturer','expert','literature')),
                source_doi VARCHAR(255) DEFAULT NULL,
                source_date DATE DEFAULT NULL,
                reliability_category TEXT DEFAULT 'medium' CHECK (reliability_category IS NULL OR reliability_category IN ('high','medium','low')),
                data_completeness REAL DEFAULT 1.0 CHECK (data_completeness IS NULL OR (data_completeness >= 0.0 AND data_completeness <= 1.0))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS ImmobilizationLayers (
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
                PC REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_type TEXT DEFAULT 'expert' CHECK (source_type IS NULL OR source_type IN ('experimental','manufacturer','expert','literature')),
                source_doi VARCHAR(255) DEFAULT NULL,
                source_date DATE DEFAULT NULL,
                reliability_category TEXT DEFAULT 'medium' CHECK (reliability_category IS NULL OR reliability_category IN ('high','medium','low')),
                data_completeness REAL DEFAULT 1.0 CHECK (data_completeness IS NULL OR (data_completeness >= 0.0 AND data_completeness <= 1.0))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS MemristiveLayers (
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
                PC REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_type TEXT DEFAULT 'expert' CHECK (source_type IS NULL OR source_type IN ('experimental','manufacturer','expert','literature')),
                source_doi VARCHAR(255) DEFAULT NULL,
                source_date DATE DEFAULT NULL,
                reliability_category TEXT DEFAULT 'medium' CHECK (reliability_category IS NULL OR reliability_category IN ('high','medium','low')),
                data_completeness REAL DEFAULT 1.0 CHECK (data_completeness IS NULL OR (data_completeness >= 0.0 AND data_completeness <= 1.0))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS SensorCombinations (
                Combo_ID VARCHAR PRIMARY KEY,
                TA_ID VARCHAR NOT NULL,
                BRE_ID VARCHAR NOT NULL,
                IM_ID VARCHAR NOT NULL,
                MEM_ID VARCHAR NOT NULL,
                SN_total REAL,
                TR_total REAL,
                ST_total REAL,
                RP_total REAL,
                LOD_total REAL,
                DR_total VARCHAR,
                HL_total REAL,
                PC_total REAL,
                Score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_test INTEGER DEFAULT 0,
                FOREIGN KEY (TA_ID) REFERENCES Analytes (TA_ID),
                FOREIGN KEY (BRE_ID) REFERENCES BioRecognitionLayers (BRE_ID),
                FOREIGN KEY (IM_ID) REFERENCES ImmobilizationLayers (IM_ID),
                FOREIGN KEY (MEM_ID) REFERENCES MemristiveLayers (MEM_ID)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS AuthUsers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(128) UNIQUE NOT NULL,
                password_hash VARCHAR(512) NOT NULL,
                role VARCHAR(64) NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_service_account INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS AuthRefreshTokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash VARCHAR(128) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                revoked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES AuthUsers (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS AuthApiKeys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                key_prefix VARCHAR(32) NOT NULL,
                key_hash VARCHAR(128) UNIQUE NOT NULL,
                revoked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES AuthUsers (id)
            );
            """
        ]
        try:
            # Создаем новое соединение для текущего потока
            with get_connection() as conn:
                cursor = conn.cursor()
                for table in tables:
                    cursor.execute(table)
                conn.commit()
                self.logger.info("Таблицы успешно созданы")
                # Ensure protective triggers use updated logic (allow deletion of test-like IDs)
                try:
                    table_id_map = {
                        "Analytes": "TA_ID",
                        "BioRecognitionLayers": "BRE_ID",
                        "ImmobilizationLayers": "IM_ID",
                        "MemristiveLayers": "MEM_ID",
                        "SensorCombinations": "Combo_ID",
                    }
                    for tbl, id_col in table_id_map.items():
                        try:
                            cursor.execute(f"PRAGMA table_info({tbl})")
                            cols = [r[1] for r in cursor.fetchall()]
                        except sqlite3.Error:
                            continue

                        if "is_test" not in cols:
                            continue

                        trigger_name = f"protect_delete_{tbl}"
                        try:
                            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
                        except sqlite3.Error:
                            pass

                        # Recreate trigger with permissive test-id matching
                        cursor.execute(f"""
                            CREATE TRIGGER {trigger_name}
                            BEFORE DELETE ON {tbl}
                            FOR EACH ROW
                            WHEN (
                                (OLD.is_test IS NULL OR OLD.is_test = 0)
                                AND (COALESCE(OLD.{id_col}, '') NOT LIKE '%_TEST%' AND COALESCE(OLD.{id_col}, '') NOT LIKE '%_DUP%' AND COALESCE(OLD.{id_col}, '') NOT LIKE '%TEST%')
                            )
                            BEGIN
                                SELECT RAISE(ABORT, 'Attempt to delete non-test data is forbidden');
                            END;
                        """)
                    conn.commit()
                except Exception:
                    # Non-fatal — triggers are protective but not critical for startup
                    pass
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка создания таблиц: {e}")

    # --- INSERT / UPSERT методы ---
    def insert_analyte(self, data: Dict[str, Any]) -> bool | str:
        """Вставка или замена аналита (создаёт новое соединение для каждого вызова)."""
        try:
            ta_id = self._resolve_value(data, 'TA_ID', 'ta_id')
            ta_name = self._resolve_value(data, 'TA_Name', 'ta_name')
            ph_min = self._resolve_value(data, 'PH_Min', 'ph_min')
            ph_max = self._resolve_value(data, 'PH_Max', 'ph_max')
            t_max = self._resolve_value(data, 'T_Max', 't_max')
            st = self._resolve_value(data, 'ST', 'stability')
            hl = self._resolve_value(data, 'HL', 'half_life')
            pc = self._resolve_value(data, 'PC', 'power_consumption')
            source_type = self._resolve_value(data, 'source_type')
            source_doi = self._resolve_value(data, 'source_doi')
            source_date = self._resolve_value(data, 'source_date')
            reliability_category = self._resolve_value(data, 'reliability_category')
            data_completeness = self._resolve_value(data, 'data_completeness')

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT TA_ID FROM Analytes WHERE TA_ID = ?", (ta_id,))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO Analytes (
                    TA_ID, TA_Name, PH_Min, PH_Max, T_Max, ST, HL, PC, is_test,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                # Normalize is_test input
                is_test_val = data.get('is_test', data.get('isTest', 0))
                try:
                    is_test_val = 1 if str(is_test_val).strip().lower() in {"1", "true", "yes", "y", "t"} else 0
                except Exception:
                    is_test_val = 0

                cursor.execute(query, (
                    ta_id, ta_name, ph_min,
                    ph_max, t_max, st,
                    hl, pc, is_test_val,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Аналит {ta_id} успешно вставлен")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка вставки аналита: {e}")
            return False
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Ошибка целостности: {e}")
            raise DatabaseIntegrityError(f"Нарушение целостности данных") from e
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка БД: {e}")
            return False

    def insert_bio_recognition_layer(self, data: Dict[str, Any]) -> bool | str:
        """Вставка или замена биораспознающего слоя (создаёт новое соединение для каждого вызова)."""
        try:
            bre_id = self._resolve_value(data, 'BRE_ID', 'bre_id')
            bre_name = self._resolve_value(data, 'BRE_Name', 'bre_name')
            ph_min = self._resolve_value(data, 'PH_Min', 'ph_min')
            ph_max = self._resolve_value(data, 'PH_Max', 'ph_max')
            t_min = self._resolve_value(data, 'T_Min', 't_min')
            t_max = self._resolve_value(data, 'T_Max', 't_max')
            sn = self._resolve_value(data, 'SN', 'sensitivity')
            dr_min = self._resolve_value(data, 'DR_Min', 'dr_min')
            dr_max = self._resolve_value(data, 'DR_Max', 'dr_max')
            rp = self._resolve_value(data, 'RP', 'reproducibility')
            tr = self._resolve_value(data, 'TR', 'response_time')
            st = self._resolve_value(data, 'ST', 'stability')
            lod = self._resolve_value(data, 'LOD', 'lod')
            hl = self._resolve_value(data, 'HL', 'durability')
            pc = self._resolve_value(data, 'PC', 'power_consumption')
            source_type = self._resolve_value(data, 'source_type')
            source_doi = self._resolve_value(data, 'source_doi')
            source_date = self._resolve_value(data, 'source_date')
            reliability_category = self._resolve_value(data, 'reliability_category')
            data_completeness = self._resolve_value(data, 'data_completeness')

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT BRE_ID FROM BioRecognitionLayers WHERE BRE_ID = ?", (bre_id,))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO BioRecognitionLayers 
                (
                    BRE_ID, BRE_Name, PH_Min, PH_Max, T_Min, T_Max, SN, DR_Min, DR_Max,
                    RP, TR, ST, LOD, HL, PC,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    bre_id, bre_name, ph_min, ph_max,
                    t_min, t_max, sn, dr_min,
                    dr_max, rp, tr, st,
                    lod, hl, pc,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Биослой {bre_id} успешно вставлен")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка вставки биослоя: {e}")
            return False
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Ошибка целостности: {e}")
            raise DatabaseIntegrityError(f"Нарушение целостности данных") from e
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка БД: {e}")
            return False

    def insert_immobilization_layer(self, data: Dict[str, Any]) -> bool | str:
        """Вставка или замена иммобилизационного слоя (создаёт новое соединение для каждого вызова)."""
        try:
            im_id = self._resolve_value(data, 'IM_ID', 'im_id')
            im_name = self._resolve_value(data, 'IM_Name', 'im_name')
            ph_min = self._resolve_value(data, 'PH_Min', 'ph_min')
            ph_max = self._resolve_value(data, 'PH_Max', 'ph_max')
            t_min = self._resolve_value(data, 'T_Min', 't_min')
            t_max = self._resolve_value(data, 'T_Max', 't_max')
            mp = self._resolve_value(data, 'MP', 'young_modulus')
            adh = self._resolve_value(data, 'Adh', 'adhesion')
            sol = self._resolve_value(data, 'Sol', 'solubility')
            k_im = self._resolve_value(data, 'K_IM', 'loss_coefficient')
            rp = self._resolve_value(data, 'RP', 'reproducibility')
            tr = self._resolve_value(data, 'TR', 'response_time')
            st = self._resolve_value(data, 'ST', 'stability')
            hl = self._resolve_value(data, 'HL', 'durability')
            pc = self._resolve_value(data, 'PC', 'power_consumption')
            source_type = self._resolve_value(data, 'source_type')
            source_doi = self._resolve_value(data, 'source_doi')
            source_date = self._resolve_value(data, 'source_date')
            reliability_category = self._resolve_value(data, 'reliability_category')
            data_completeness = self._resolve_value(data, 'data_completeness')

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT IM_ID FROM ImmobilizationLayers WHERE IM_ID = ?", (im_id,))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO ImmobilizationLayers 
                (
                    IM_ID, IM_Name, PH_Min, PH_Max, T_Min, T_Max, MP, Adh, Sol, K_IM,
                    RP, TR, ST, HL, PC,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    im_id, im_name, ph_min, ph_max,
                    t_min, t_max, mp, adh,
                    sol, k_im, rp, tr,
                    st, hl, pc,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Иммобилизационный слой {im_id} успешно вставлен")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка вставки иммобилизационного слоя: {e}")
            return False
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Ошибка целостности: {e}")
            raise DatabaseIntegrityError(f"Нарушение целостности данных") from e
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка БД: {e}")
            return False

    def insert_memristive_layer(self, data: Dict[str, Any]) -> bool | str:
        """Вставка или замена мемристивного слоя (создаёт новое соединение для каждого вызова)."""
        try:
            mem_id = self._resolve_value(data, 'MEM_ID', 'mem_id')
            mem_name = self._resolve_value(data, 'MEM_Name', 'mem_name')
            ph_min = self._resolve_value(data, 'PH_Min', 'ph_min')
            ph_max = self._resolve_value(data, 'PH_Max', 'ph_max')
            t_min = self._resolve_value(data, 'T_Min', 't_min')
            t_max = self._resolve_value(data, 'T_Max', 't_max')
            mp = self._resolve_value(data, 'MP', 'young_modulus')
            sn = self._resolve_value(data, 'SN', 'sensitivity')
            dr_min = self._resolve_value(data, 'DR_Min', 'dr_min')
            dr_max = self._resolve_value(data, 'DR_Max', 'dr_max')
            rp = self._resolve_value(data, 'RP', 'reproducibility')
            tr = self._resolve_value(data, 'TR', 'response_time')
            st = self._resolve_value(data, 'ST', 'stability')
            lod = self._resolve_value(data, 'LOD', 'lod')
            hl = self._resolve_value(data, 'HL', 'durability')
            pc = self._resolve_value(data, 'PC', 'power_consumption')
            source_type = self._resolve_value(data, 'source_type')
            source_doi = self._resolve_value(data, 'source_doi')
            source_date = self._resolve_value(data, 'source_date')
            reliability_category = self._resolve_value(data, 'reliability_category')
            data_completeness = self._resolve_value(data, 'data_completeness')

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MEM_ID FROM MemristiveLayers WHERE MEM_ID = ?", (mem_id,))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO MemristiveLayers 
                (
                    MEM_ID, MEM_Name, PH_Min, PH_Max, T_Min, T_Max, MP, SN, DR_Min, DR_Max,
                    RP, TR, ST, LOD, HL, PC,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    mem_id, mem_name, ph_min, ph_max,
                    t_min, t_max, mp, sn,
                    dr_min, dr_max, rp, tr,
                    st, lod, hl, pc,
                    source_type, source_doi, source_date, reliability_category, data_completeness
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Мемристивный слой {mem_id} успешно вставлен")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка вставки мемристивного слоя: {e}")
            return False
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Ошибка целостности: {e}")
            raise DatabaseIntegrityError(f"Нарушение целостности данных") from e
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка БД: {e}")
            return False


    def insert_sensor_combination(self, data: Dict[str, Any]) -> bool | str:
        """Вставка или замена комбинации сенсора (создаёт новое соединение для каждого вызова)."""
        try:
            combo_id = self._resolve_value(data, 'Combo_ID', 'combo_id')
            ta_id = self._resolve_value(data, 'TA_ID', 'ta_id')
            bre_id = self._resolve_value(data, 'BRE_ID', 'bre_id')
            im_id = self._resolve_value(data, 'IM_ID', 'im_id')
            mem_id = self._resolve_value(data, 'MEM_ID', 'mem_id')
            sn_total = self._resolve_value(data, 'SN_total', 'sn_total')
            tr_total = self._resolve_value(data, 'TR_total', 'tr_total')
            st_total = self._resolve_value(data, 'ST_total', 'st_total')
            rp_total = self._resolve_value(data, 'RP_total', 'rp_total')
            lod_total = self._resolve_value(data, 'LOD_total', 'lod_total')
            dr_total = self._resolve_value(data, 'DR_total', 'dr_total')
            hl_total = self._resolve_value(data, 'HL_total', 'hl_total')
            pc_total = self._resolve_value(data, 'PC_total', 'pc_total')
            score = self._resolve_value(data, 'Score', 'score')
            created_at = self._resolve_value(data, 'created_at')

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Combo_ID FROM SensorCombinations WHERE Combo_ID = ?", (combo_id,))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO SensorCombinations 
                (Combo_ID, TA_ID, BRE_ID, IM_ID, MEM_ID, SN_total, TR_total, ST_total, RP_total, LOD_total, DR_total, HL_total, PC_total, Score, created_at, is_test)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    combo_id, ta_id, bre_id, im_id,
                    mem_id, sn_total, tr_total, st_total,
                    rp_total, lod_total, dr_total, hl_total,
                    pc_total, score, created_at, data.get('is_test', 0)
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Комбинация сенсора {combo_id} успешно вставлена")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка вставки комбинации сенсора: {e}")
            return False
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Ошибка целостности: {e}")
            raise DatabaseIntegrityError(f"Нарушение целостности данных") from e
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка БД: {e}")
            return False

    def delete_sensor_combinations(
        self,
        combo_ids: List[str] | None = None,
        only_test: bool = True,
        allow_non_test: bool = False,
    ) -> int:
        """Безопасное удаление комбинаций из SensorCombinations.

        По умолчанию удаляются только тестовые комбинации: либо те, где `is_test = 1`,
        либо те, чей `Combo_ID`/связанные ID содержат суффиксы `_TEST` или `_DUP`.
        При `allow_non_test=True` можно явно удалить и нетестовые комбинации.
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                column_exists = False
                try:
                    cursor.execute("PRAGMA table_info(SensorCombinations)")
                    column_exists = any(row[1] == "is_test" for row in cursor.fetchall())
                except sqlite3.Error:
                    column_exists = False

                if combo_ids:
                    placeholders = ", ".join("?" for _ in combo_ids)
                    where_clause = f"Combo_ID IN ({placeholders})"
                    params: List[Any] = list(combo_ids)
                else:
                    where_clause = "1=1"
                    params = []

                if only_test and not allow_non_test:
                    test_predicate = "Combo_ID LIKE '%TEST%' OR Combo_ID LIKE '%_DUP%' OR Combo_ID LIKE '%_TEST%'"
                    if column_exists:
                        test_predicate = f"({test_predicate} OR is_test = 1)"
                    where_clause += f" AND ({test_predicate})"

                if only_test and not allow_non_test and column_exists:
                    cursor.execute(
                        f"UPDATE SensorCombinations SET is_test = 1 WHERE {where_clause}",
                        params,
                    )

                cursor.execute(
                    f"DELETE FROM SensorCombinations WHERE {where_clause}",
                    params,
                )
                conn.commit()
                self.clear_cache()
                deleted_count = cursor.rowcount
                self.logger.info(
                    f"Удалено {deleted_count} комбинаций из SensorCombinations"
                )
                return deleted_count
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка удаления комбинаций сенсоров: {e}")
            return 0

    # --- LIST методы с кэшем ---
    @lru_cache(maxsize=32)
    def list_all_analytes(self) -> List[Dict[str, Any]]:
        """Получение всех аналитов с выбором конкретных столбцов."""
        query = """
        SELECT TA_ID, TA_Name, PH_Min, PH_Max, T_Max, ST, is_test
        FROM Analytes
        ORDER BY TA_Name
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} аналитов")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения аналитов: {e}")
            return []

    @lru_cache(maxsize=32)
    def list_all_bio_recognition_layers(self) -> List[Dict[str, Any]]:
        """Получение всех биораспознающих слоев."""
        query = """
        SELECT BRE_ID, BRE_Name, PH_Min, PH_Max, T_Min, T_Max, SN
        FROM BioRecognitionLayers
        ORDER BY BRE_Name
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} биослоев")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения биослоев: {e}")
            return []

    @lru_cache(maxsize=32)
    def list_all_immobilization_layers(self) -> List[Dict[str, Any]]:
        """Получение всех иммобилизационных слоев."""
        query = """
        SELECT IM_ID, IM_Name, PH_Min, PH_Max, T_Min, T_Max, MP
        FROM ImmobilizationLayers
        ORDER BY IM_Name
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} иммобилизационных слоев")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения иммобилизационных слоев: {e}")
            return []

    @lru_cache(maxsize=32)
    def list_all_memristive_layers(self) -> List[Dict[str, Any]]:
        """Получение всех мемристивных слоев."""
        query = """
        SELECT MEM_ID, MEM_Name, PH_Min, PH_Max, T_Min, T_Max, SN
        FROM MemristiveLayers
        ORDER BY MEM_Name
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} мемристивных слоев")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения мемристивных слоев: {e}")
            return []

    @lru_cache(maxsize=32)
    def list_all_sensor_combinations(self) -> List[Dict[str, Any]]:
        """Получение всех комбинаций сенсоров."""
        query = """
        SELECT Combo_ID, TA_ID, BRE_ID, IM_ID, MEM_ID, Score
        FROM SensorCombinations
        ORDER BY Combo_ID
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} комбинаций сенсоров")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения комбинаций сенсоров: {e}")
            return []

    def insert_bio_recognition(self, data: Dict[str, Any]) -> bool | str:
        return self.insert_bio_recognition_layer(data)

    def insert_immobilization(self, data: Dict[str, Any]) -> bool | str:
        return self.insert_immobilization_layer(data)

    def insert_memristive(self, data: Dict[str, Any]) -> bool | str:
        return self.insert_memristive_layer(data)

    def get_combinations(self) -> List[Dict[str, Any]]:
        return self.list_all_sensor_combinations()
   
    def _fetch_paginated(
        self, 
        table_config: TableConfig, 
        limit: int, 
        offset: int
    ) -> List[Dict[str, Any]]:
        """Универсальный метод пагинации для любой таблицы."""
        cols = table_config["select_cols"]
        cols_str = ", ".join(cols)
        order_by = table_config["display_col"]
        
        query = f"""
        SELECT {cols_str}
        FROM {table_config["table"]}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(
                    f"Получено {len(results)} {table_config['entity_name_plural']} (страница)"
                )
                return results
        except sqlite3.Error as e:
            self.logger.error(
                f"Ошибка получения {table_config['entity_name_plural']} с пагинацией: {e}"
            )
            return []

    def _fetch_by_id(
        self,
        table_config: TableConfig,
        id_value: str
    ) -> Dict[str, Any] | None:
        """Универсальный метод получения записи по ID."""
        cols = table_config["all_cols"]
        cols_str = ", ".join(cols)
        id_col = table_config["id_col"]
        
        query = f"""
        SELECT {cols_str}
        FROM {table_config["table"]}
        WHERE {id_col} = ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (id_value,))
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    self.logger.info(
                        f"Получен {table_config['entity_name']} {id_value}"
                    )
                    return dict(zip(columns, result))
                return None
        except sqlite3.Error as e:
            self.logger.error(
                f"Ошибка получения {table_config['entity_name']} {id_value}: {e}"
            )
            return None

    # === ПУБЛИЧНЫЕ МЕТОДЫ (обёртки над параметризованными) ===
    
    def list_all_analytes_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение аналитов с пагинацией."""
        return self._fetch_paginated(TableConfig.ANALYTES, limit, offset)

    def list_all_bio_recognition_layers_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение биослоев с пагинацией."""
        return self._fetch_paginated(TableConfig.BIO_RECOGNITION, limit, offset)

    def list_all_immobilization_layers_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение иммобилизационных слоев с пагинацией."""
        return self._fetch_paginated(TableConfig.IMMOBILIZATION, limit, offset)

    def list_all_memristive_layers_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение мемристивных слоев с пагинацией."""
        return self._fetch_paginated(TableConfig.MEMRISTIVE, limit, offset)

    def list_all_sensor_combinations_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение комбинаций сенсоров с пагинацией."""
        return self._fetch_paginated(TableConfig.SENSOR_COMBINATIONS, limit, offset)

    def get_analyte_by_id(self, ta_id: str) -> Dict[str, Any] | None:
        """Получение аналита по ID."""
        return self._fetch_by_id(TableConfig.ANALYTES, ta_id)

    def get_bio_recognition_layer_by_id(self, bre_id: str) -> Dict[str, Any] | None:
        """Получение биораспознающего слоя по ID."""
        return self._fetch_by_id(TableConfig.BIO_RECOGNITION, bre_id)

    def get_immobilization_layer_by_id(self, im_id: str) -> Dict[str, Any] | None:
        """Получение иммобилизационного слоя по ID."""
        return self._fetch_by_id(TableConfig.IMMOBILIZATION, im_id)

    def get_memristive_layer_by_id(self, mem_id: str) -> Dict[str, Any] | None:
        """Получение мемристивного слоя по ID."""
        return self._fetch_by_id(TableConfig.MEMRISTIVE, mem_id)

    def clear_cache(self):
        """Очистка кэша результатов запросов."""
        self.list_all_analytes.cache_clear()
        self.list_all_bio_recognition_layers.cache_clear()
        self.list_all_immobilization_layers.cache_clear()
        self.list_all_memristive_layers.cache_clear()
        self.list_all_sensor_combinations.cache_clear()
        self.logger.info("Кэш очищен")
        
    def analyte_exists(self, field: str, value: Any) -> bool:
        query = f"""
        SELECT EXISTS(
            SELECT 1 FROM {TableConfig.ANALYTES["table"]}
            WHERE {field} = ?
        )
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (value,))
                return cursor.fetchone()[0] == 1
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка проверки существования аналита: {e}")
            return False

    def bio_recognition_exists(self, field: str, value: Any) -> bool:
        query = f"""
        SELECT EXISTS(
            SELECT 1 FROM {TableConfig.BIO_RECOGNITION["table"]}
            WHERE {field} = ?
        )
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (value,))
                return cursor.fetchone()[0] == 1
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка проверки существования биослоя: {e}")
            return False
    def immobilization_exists(self, field: str, value: Any) -> bool:
        query = f"""
        SELECT EXISTS(
            SELECT 1 FROM {TableConfig.IMMOBILIZATION["table"]}
            WHERE {field} = ?
        )
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (value,))
                return cursor.fetchone()[0] == 1
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка проверки существования иммобилизационного слоя: {e}")
            return False

    def memristive_exists(self, field: str, value: Any) -> bool:
        query = f"""
        SELECT EXISTS(
            SELECT 1 FROM {TableConfig.MEMRISTIVE["table"]}
            WHERE {field} = ?
        )
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (value,))
                return cursor.fetchone()[0] == 1
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка проверки существования мемристивного слоя: {e}")
            return False

    # Field mappings from snake_case API format to DB column format
    _FIELD_MAP = {
        'analyte': {
            'ta_id': 'TA_ID', 'ta_name': 'TA_Name', 'ph_min': 'PH_Min', 'ph_max': 'PH_Max',
            't_max': 'T_Max', 'stability': 'ST', 'half_life': 'HL', 'power_consumption': 'PC',
        },
        'bio_recognition': {
            'bre_id': 'BRE_ID', 'bre_name': 'BRE_Name', 'ph_min': 'PH_Min', 'ph_max': 'PH_Max',
            't_min': 'T_Min', 't_max': 'T_Max', 'sensitivity': 'SN', 'dr_min': 'DR_Min',
            'dr_max': 'DR_Max', 'reproducibility': 'RP', 'response_time': 'TR', 'stability': 'ST',
            'lod': 'LOD', 'durability': 'HL', 'power_consumption': 'PC',
        },
        'immobilization': {
            'im_id': 'IM_ID', 'im_name': 'IM_Name', 'ph_min': 'PH_Min', 'ph_max': 'PH_Max',
            't_min': 'T_Min', 't_max': 'T_Max', 'young_modulus': 'MP', 'adhesion': 'Adh',
            'solubility': 'Sol', 'loss_coefficient': 'K_IM', 'reproducibility': 'RP',
            'response_time': 'TR', 'stability': 'ST', 'durability': 'HL', 'power_consumption': 'PC',
        },
        'memristive': {
            'mem_id': 'MEM_ID', 'mem_name': 'MEM_Name', 'ph_min': 'PH_Min', 'ph_max': 'PH_Max',
            't_min': 'T_Min', 't_max': 'T_Max', 'young_modulus': 'MP', 'sensitivity': 'SN',
            'dr_min': 'DR_Min', 'dr_max': 'DR_Max', 'reproducibility': 'RP', 'response_time': 'TR',
            'stability': 'ST', 'lod': 'LOD', 'durability': 'HL', 'power_consumption': 'PC',
        },
    }

    # DatabaseAdapter methods implementation
    def insert(self, entity_type: str, data: Dict[str, Any]) -> Any:
        """Универсальный insert на основе специфичных методов"""
        methods = {
            'analyte': self.insert_analyte,
            'bio_recognition': self.insert_bio_recognition_layer,
            'immobilization': self.insert_immobilization_layer,
            'memristive': self.insert_memristive_layer,
        }

        insert_method = methods.get(entity_type)
        if not insert_method:
            return f"Неизвестный тип: {entity_type}"

        # Convert snake_case API keys to DB column format if needed
        field_map = self._FIELD_MAP.get(entity_type, {})
        if field_map:
            data = {field_map.get(k, k): v for k, v in data.items()}

        return insert_method(data)
    
    def list_all_paginated(self, entity_type: str, limit: int, offset: int) -> List[Dict]:
        methods = {
            'analyte': self.list_all_analytes_paginated,
            'bio_recognition': self.list_all_bio_recognition_layers_paginated,
            'immobilization': self.list_all_immobilization_layers_paginated,
            'memristive': self.list_all_memristive_layers_paginated,
        }
        
        list_method = methods.get(entity_type)
        if list_method:
            return list_method(limit, offset)
        return []
    
    def entity_exists(self, entity_type: str, field: str, value: Any) -> bool:
        exists_methods = {
            'analyte': self.analyte_exists,
            'bio_recognition': self.bio_recognition_exists,
            'immobilization': self.immobilization_exists,
            'memristive': self.memristive_exists,
        }
        method = exists_methods.get(entity_type)
        return method(field, value) if method else False
    
    async def close(self) -> None:
        """Освобождает ресурсы при завершении работы."""
        if hasattr(self, '_cache'):
            self._cache.clear()
        if hasattr(self, 'cache'):
            self.cache.clear()
        logger.info("🔒 DatabaseManager shutting down")
    