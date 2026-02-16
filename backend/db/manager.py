# db/manager.py
import sqlite3
from enum import Enum
from typing import Dict, Any, List
import logging
from functools import lru_cache

from db.exceptions import DatabaseConnectionError, DatabaseIntegrityError
from db.migrations import MigrationManager, ALL_MIGRATIONS

from services.biosensor_service import DatabaseAdapter

DB_NAME = "memristive_biosensor.db"

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

    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.logger = logger
        
         # Применить миграции ПЕРЕД созданием таблиц
        migrator = MigrationManager(db_name)
        migrator.migrate(ALL_MIGRATIONS)
        
        try:
            self.create_tables()
        except sqlite3.Error as e:
            self.logger.critical(f"Не удалось инициализировать БД: {e}")
            raise DatabaseConnectionError(f"Ошибка подключения к {db_name}") from e

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                FOREIGN KEY (TA_ID) REFERENCES Analytes (TA_ID),
                FOREIGN KEY (BRE_ID) REFERENCES BioRecognitionLayers (BRE_ID),
                FOREIGN KEY (IM_ID) REFERENCES ImmobilizationLayers (IM_ID),
                FOREIGN KEY (MEM_ID) REFERENCES MemristiveLayers (MEM_ID)
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
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка создания таблиц: {e}")

    # --- INSERT / UPSERT методы ---
    def insert_analyte(self, data: Dict[str, Any]) -> bool | str:
        """Вставка или замена аналита (создаёт новое соединение для каждого вызова)."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT TA_ID FROM Analytes WHERE TA_ID = ?", (data['TA_ID'],))
                if cursor.fetchone():
                    return "DUPLICATE"  # Сигнал о дубликате

                query = """
                INSERT OR REPLACE INTO Analytes (TA_ID, TA_Name, PH_Min, PH_Max, T_Max, ST, HL, PC)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    data['TA_ID'], data['TA_Name'], data.get('PH_Min'),
                    data.get('PH_Max'), data.get('T_Max'), data.get('ST'),
                    data.get('HL'), data.get('PC')
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Аналит {data['TA_ID']} успешно вставлен")
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
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT BRE_ID FROM BioRecognitionLayers WHERE BRE_ID = ?", (data['BRE_ID'],))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO BioRecognitionLayers 
                (BRE_ID, BRE_Name, PH_Min, PH_Max, T_Min, T_Max, SN, DR_Min, DR_Max, RP, TR, ST, LOD, HL, PC)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    data['BRE_ID'], data['BRE_Name'], data.get('PH_Min'), data.get('PH_Max'),
                    data.get('T_Min'), data.get('T_Max'), data.get('SN'), data.get('DR_Min'),
                    data.get('DR_Max'), data.get('RP'), data.get('TR'), data.get('ST'),
                    data.get('LOD'), data.get('HL'), data.get('PC')
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Биослой {data['BRE_ID']} успешно вставлен")
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
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT IM_ID FROM ImmobilizationLayers WHERE IM_ID = ?", (data['IM_ID'],))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO ImmobilizationLayers 
                (IM_ID, IM_Name, PH_Min, PH_Max, T_Min, T_Max, MP, Adh, Sol, K_IM, RP, TR, ST, HL, PC)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    data['IM_ID'], data['IM_Name'], data.get('PH_Min'), data.get('PH_Max'),
                    data.get('T_Min'), data.get('T_Max'), data.get('MP'), data.get('Adh'),
                    data.get('Sol'), data.get('K_IM'), data.get('RP'), data.get('TR'),
                    data.get('ST'), data.get('HL'), data.get('PC')
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Иммобилизационный слой {data['IM_ID']} успешно вставлен")
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
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MEM_ID FROM MemristiveLayers WHERE MEM_ID = ?", (data['MEM_ID'],))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO MemristiveLayers 
                (MEM_ID, MEM_Name, PH_Min, PH_Max, T_Min, T_Max, MP, SN, DR_Min, DR_Max, RP, TR, ST, LOD, HL, PC)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    data['MEM_ID'], data['MEM_Name'], data.get('PH_Min'), data.get('PH_Max'),
                    data.get('T_Min'), data.get('T_Max'), data.get('MP'), data.get('SN'),
                    data.get('DR_Min'), data.get('DR_Max'), data.get('RP'), data.get('TR'),
                    data.get('ST'), data.get('LOD'), data.get('HL'), data.get('PC')
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Мемристивный слой {data['MEM_ID']} успешно вставлен")
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
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Combo_ID FROM SensorCombinations WHERE Combo_ID = ?", (data['Combo_ID'],))
                if cursor.fetchone():
                    return "DUPLICATE"

                query = """
                INSERT OR REPLACE INTO SensorCombinations 
                (Combo_ID, TA_ID, BRE_ID, IM_ID, MEM_ID, SN_total, TR_total, ST_total, RP_total, LOD_total, DR_total, HL_total, PC_total, Score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    data['Combo_ID'], data.get('TA_ID'), data.get('BRE_ID'), data.get('IM_ID'),
                    data.get('MEM_ID'), data.get('SN_total'), data.get('TR_total'), data.get('ST_total'),
                    data.get('RP_total'), data.get('LOD_total'), data.get('DR_total'), data.get('HL_total'),
                    data.get('PC_total'), data.get('Score'), data.get('created_at')
                ))
                conn.commit()
                self.clear_cache()
                self.logger.info(f"Комбинация сенсора {data['Combo_ID']} успешно вставлена")
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

    # --- LIST методы с кэшем ---
    @lru_cache(maxsize=32)
    def list_all_analytes(self) -> List[Dict[str, Any]]:
        """Получение всех аналитов с выбором конкретных столбцов."""
        query = """
        SELECT TA_ID, TA_Name, PH_Min, PH_Max, T_Max, ST
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
    
    
    