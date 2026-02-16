import sqlite3
from typing import Dict, Any, List
import json
from functools import lru_cache
import logging

import streamlit as st
import atexit

import math

# Настройка логирования
logging.basicConfig(level=logging.INFO, filename='biosensor.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_connection():
    return sqlite3.connect("memristive_biosensor.db")


def debug(message):
    # st.write(f"DEBUG: {message}")
    print(f"DEBUG: {message}")


class DatabaseManager:
    """Класс для управления операциями с базой данных SQLite для приложения BiosensorGUI."""
    def __init__(self, db_name="memristive_biosensor.db"):
        self.db_name = db_name
        self.logger = logging.getLogger(__name__)  # Инициализируем логгер ПЕРВЫМ
        
        # self.conn = sqlite3.connect(db_name)
        conn = get_connection()
        conn.execute("PRAGMA foreign_keys = ON")  # Включение поддержки внешних ключей
        conn.close()

        self.create_tables()

    def create_tables(self):
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
    
    """Управление БД - БЕЗ Streamlit вызовов"""
    def insert_analyte(self, data: Dict[str, Any]) -> bool:
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
    
    """Управление БД - БЕЗ Streamlit вызовов"""
    def insert_bio_recognition_layer(self, data: Dict[str, Any]) -> bool:
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

    """Управление БД - БЕЗ Streamlit вызовов"""
    def insert_immobilization_layer(self, data: Dict[str, Any]) -> bool:
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

    def insert_memristive_layer(self, data: Dict[str, Any]) -> bool:
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

    def insert_sensor_combination(self, data: Dict[str, Any]) -> bool:
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

    def list_all_analytes_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение аналитов с пагинацией."""
        query = """
        SELECT TA_ID, TA_Name, PH_Min, PH_Max, T_Max, ST
        FROM Analytes
        ORDER BY TA_Name
        LIMIT ? OFFSET ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} аналитов (страница)")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения аналитов с пагинацией: {e}")
            return []

    def list_all_bio_recognition_layers_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение биослоев с пагинацией."""
        query = """
        SELECT BRE_ID, BRE_Name, PH_Min, PH_Max, T_Min, T_Max, SN
        FROM BioRecognitionLayers
        ORDER BY BRE_Name
        LIMIT ? OFFSET ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} биослоев (страница)")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения биослоев с пагинацией: {e}")
            return []

    def list_all_immobilization_layers_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение иммобилизационных слоев с пагинацией."""
        query = """
        SELECT IM_ID, IM_Name, PH_Min, PH_Max, T_Min, T_Max, MP
        FROM ImmobilizationLayers
        ORDER BY IM_Name
        LIMIT ? OFFSET ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} иммобилизационных слоев (страница)")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения иммобилизационных слоев с пагинацией: {e}")
            return []

    def list_all_memristive_layers_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение мемристивных слоев с пагинацией."""
        query = """
        SELECT MEM_ID, MEM_Name, PH_Min, PH_Max, T_Min, T_Max, SN
        FROM MemristiveLayers
        ORDER BY MEM_Name
        LIMIT ? OFFSET ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} мемристивных слоев (страница)")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения мемристивных слоев с пагинацией: {e}")
            return []
    
    def list_all_sensor_combinations_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Получение всех комбинаций сенсоров."""
        query = """
        SELECT Combo_ID, TA_ID, BRE_ID, IM_ID, MEM_ID, Score
        FROM SensorCombinations
        ORDER BY Combo_ID
        LIMIT ? OFFSET ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.logger.info(f"Получено {len(results)} комбинаций сенсоров (страница)")
                return results
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения комбинаций сенсоров с пагинацией: {e}")
            return []

    def get_analyte_by_id(self, ta_id: str) -> Dict[str, Any]:
        """Получение аналита по ID."""
        query = """
        SELECT TA_ID, TA_Name, PH_Min, PH_Max, T_Max, ST, HL, PC
        FROM Analytes
        WHERE TA_ID = ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (ta_id,))
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    self.logger.info(f"Получен аналит {ta_id}")
                    return dict(zip(columns, result))
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения аналита {ta_id}: {e}")
            return None

    def get_bio_recognition_layer_by_id(self, bre_id: str) -> Dict[str, Any]:
        """Получение биораспознающего слоя по ID."""
        query = """
        SELECT BRE_ID, BRE_Name, PH_Min, PH_Max, T_Min, T_Max, SN, DR_Min, DR_Max, RP, TR, ST, LOD, HL, PC
        FROM BioRecognitionLayers
        WHERE BRE_ID = ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (bre_id,))
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    self.logger.info(f"Получен биослой {bre_id}")
                    return dict(zip(columns, result))
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения биослоя {bre_id}: {e}")
            return None

    def get_immobilization_layer_by_id(self, im_id: str) -> Dict[str, Any]:
        """Получение иммобилизационного слоя по ID."""
        query = """
        SELECT IM_ID, IM_Name, PH_Min, PH_Max, T_Min, T_Max, MP, Adh, Sol, K_IM, RP, TR, ST, HL, PC
        FROM ImmobilizationLayers
        WHERE IM_ID = ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (im_id,))
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    self.logger.info(f"Получен иммобилизационный слой {im_id}")
                    return dict(zip(columns, result))
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения иммобилизационного слоя {im_id}: {e}")
            return None

    def get_memristive_layer_by_id(self, mem_id: str) -> Dict[str, Any]:
        """Получение мемристивного слоя по ID."""
        query = """
        SELECT MEM_ID, MEM_Name, PH_Min, PH_Max, T_Min, T_Max, MP, SN, DR_Min, DR_Max, RP, TR, ST, LOD, HL, PC
        FROM MemristiveLayers
        WHERE MEM_ID = ?
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (mem_id,))
                result = cursor.fetchone()
                if result:
                    columns = [description[0] for description in cursor.description]
                    self.logger.info(f"Получен мемристивный слой {mem_id}")
                    return dict(zip(columns, result))
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения мемристивного слоя {mem_id}: {e}")
            return None

    def clear_cache(self):
        """Очистка кэша результатов запросов."""
        self.list_all_analytes.cache_clear()
        self.list_all_bio_recognition_layers.cache_clear()
        self.list_all_immobilization_layers.cache_clear()
        self.list_all_memristive_layers.cache_clear()
        self.list_all_sensor_combinations.cache_clear()
        self.logger.info("Кэш очищен")


class BiosensorGUI:
    """GUI-приложение для управления паспортами мемристивных биосенсоров."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        st.set_page_config(page_title="Паспорта мемристивных биосенсоров v2.0", layout="wide")
        st.title("Паспорта мемристивных биосенсоров v2.0")

        # Инициализация базы данных
        self.db_manager = DatabaseManager()

        # ✅ Инициализируем session_state для управления UI
        if 'active_section' not in st.session_state:
            st.session_state.active_section = 'data_entry'  # 'data_entry', 'database', 'analysis', 'about'
        
        if 'page_size' not in st.session_state:
            st.session_state.page_size = 50
        
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0

        # Настройки пагинации
        self.page_size = 50
        self.current_page = 0
        self.current_data_type = 'analytes'  # Для отслеживания текущего типа данных в Treeview

        # Запись значений в session_state, чтобы они сохранялись между перерисовками Streamlit
        st.session_state.setdefault('page_size', self.page_size)
        st.session_state.setdefault('current_page', self.current_page)
        st.session_state.setdefault('current_data_type', self.current_data_type)

        # Загрузка конфигурации или создание значений по умолчанию
        self.config = self.get_default_config()

        # Ограничения для валидации полей
        self.field_constraints = {
            'analyte': {
                'ph_min': {'min': 2.0, 'max': 10.0},  # Расширили диапазон
                'ph_max': {'min': 2.0, 'max': 10.0},  # Расширили диапазон
                't_max': {'min': 0, 'max': 180},
                'stability': {'min': 0, 'max': 365},
                'half_life': {'min': 0, 'max': 8760},
                'power_consumption': {'min': 0, 'max': 1000}
            },
            'bio_recognition': {
                'ph_min': {'min': 2.0, 'max': 10.0},  # Расширили диапазон
                'ph_max': {'min': 2.0, 'max': 10.0},  # Расширили диапазон
                't_min': {'min': 4, 'max': 120},
                't_max': {'min': 4, 'max': 120},
                'dr_min': {'min': 0.1, 'max': 1000000000000},
                'dr_max': {'min': 0.1, 'max': 1000000000000},
                'sensitivity': {'min': 0, 'max': 20000},
                'reproducibility': {'min': 0, 'max': 100},
                'response_time': {'min': 0, 'max': 3600},
                'stability': {'min': 0, 'max': 365},
                'lod': {'min': 0, 'max': 50000},
                'durability': {'min': 0, 'max': 8760},
                'power_consumption': {'min': 0, 'max': 1000}
            },
            'immobilization': {
                'ph_min': {'min': 2.0, 'max': 10.0},  # Расширили диапазон
                'ph_max': {'min': 2.0, 'max': 10.0},  # Расширили диапазон
                't_min': {'min': 4, 'max': 120},
                't_max': {'min': 4, 'max': 120},
                'young_modulus': {'min': 0, 'max': 1000},
                # 'adhesion': {'min': 0, 'max': 100}, # замена на строчный тип
                # 'solubility': {'min': 0, 'max': 100}, # замена на строчный тип
                'loss_coefficient': {'min': 0, 'max': 1},
                'reproducibility': {'min': 0, 'max': 100},
                'response_time': {'min': 0, 'max': 3600},
                'stability': {'min': 0, 'max': 365},
                'durability': {'min': 0, 'max': 8760},
                'power_consumption': {'min': 0, 'max': 1000}
            },
            'memristive': {
                'ph_min': {'min': 2.0, 'max': 10.0},
                'ph_max': {'min': 2.0, 'max': 10.0},
                't_min': {'min': 5, 'max': 120},
                't_max': {'min': 5, 'max': 120},
                'dr_min': {'min': 0.0000001, 'max': 100000000000},
                'dr_max': {'min': 0.0000001, 'max': 100000000000},
                'young_modulus': {'min': 0, 'max': 1000},
                'sensitivity': {'min': 0, 'max': 1000},
                'reproducibility': {'min': 0, 'max': 100},
                'response_time': {'min': 0, 'max': 3600},
                'stability': {'min': 0, 'max': 365},
                'lod': {'min': 0, 'max': 100000},
                'durability': {'min': 0, 'max': 100000},
                'power_consumption': {'min': 0, 'max': 1000}
            }
        }

        # Создание интерфейса
        self.sections = {}

    @staticmethod
    def get_default_config():
        """Возвращает конфигурацию по умолчанию для полей."""
        return {
            'analyte': [
                {'label': 'ID аналита:', 'var_name': 'ta_id', 'hint': 'Например: TA001'},
                {'label': 'Название:', 'var_name': 'ta_name', 'hint': 'Полное название аналита'},
                {'label': 'pH диапазон:', 'type': 'range', 'min_var': 'ph_min', 'max_var': 'ph_max', 'hint': '2.0 — 10.0'},
                {'label': 'Макс. температура (°C):', 'var_name': 't_max', 'hint': '0-180'},
                {'label': 'Стабильность (дни):', 'var_name': 'stability', 'hint': '0-365'},
                {'label': 'Период полураспада (ч):', 'var_name': 'half_life', 'hint': '0-8760'},
                {'label': 'Энергопотребление (мВт):', 'var_name': 'power_consumption', 'hint': '0-1000'}
            ],
            'bio_recognition': [
                {'label': 'ID биослоя:', 'var_name': 'bre_id', 'hint': 'Например: BRE001'},
                {'label': 'Название:', 'var_name': 'bre_name', 'hint': 'Тип биослоя'},
                {'label': 'pH диапазон:', 'type': 'range', 'min_var': 'ph_min', 'max_var': 'ph_max', 'hint': '2.0 — 10.0'},
                {'label': 'Температурный диапазон (°C):', 'type': 'range', 'min_var': 't_min', 'max_var': 't_max', 'hint': '2 — 120'},
                {'label': 'Диапазон измерений (пМ):', 'type': 'range', 'min_var': 'dr_min', 'max_var': 'dr_max', 'hint': '0.1 — 1*10^12'},
                {'label': 'Чувствительность (мкА/(мкМ*см^2)):', 'var_name': 'sensitivity', 'hint': '0.01 — 1000'},
                {'label': 'Воспроизводимость (%):', 'var_name': 'reproducibility', 'hint': '0-100'},
                {'label': 'Время отклика (с):', 'var_name': 'response_time', 'hint': '0-3600'},
                {'label': 'Стабильность (дни):', 'var_name': 'stability', 'hint': '0-365'},
                {'label': 'Предел обнаружения (нМ):', 'var_name': 'lod', 'hint': '0-100000'},
                {'label': 'Долговечность (ч):', 'var_name': 'durability', 'hint': '0-100000'},
                {'label': 'Энергопотребление (мВт):', 'var_name': 'power_consumption', 'hint': '0-1000'}
            ],
            'immobilization': [
                {'label': 'ID иммобилизации:', 'var_name': 'im_id', 'hint': 'Например: IM001'},
                {'label': 'Название:', 'var_name': 'im_name', 'hint': 'Тип иммобилизации'},
                {'label': 'pH диапазон:', 'type': 'range', 'min_var': 'ph_min', 'max_var': 'ph_max', 'hint': '2.0 — 10.0'},
                {'label': 'Температурный диапазон (°C):', 'type': 'range', 'min_var': 't_min', 'max_var': 't_max', 'hint': '4 — 95'},
                {'label': 'Модуль Юнга (ГПа):', 'var_name': 'young_modulus', 'hint': '0-1000'},
                {'label': 'Адгезия (%):', 'var_name': 'adhesion', 'hint': 'Например: высокая'},
                {'label': 'Растворимость (%):', 'var_name': 'solubility', 'hint': 'Например: средняя'},
                {'label': 'Коэффициент потерь:', 'var_name': 'loss_coefficient', 'hint': '0-1'},
                {'label': 'Воспроизводимость (%):', 'var_name': 'reproducibility', 'hint': '0-100'},
                {'label': 'Время отклика (с):', 'var_name': 'response_time', 'hint': '0-3600'},
                {'label': 'Стабильность (дни):', 'var_name': 'stability', 'hint': '0-365'},
                {'label': 'Долговечность (ч):', 'var_name': 'durability', 'hint': '0-8760'},
                {'label': 'Энергопотребление (мВт):', 'var_name': 'power_consumption', 'hint': '0-1000'}
            ],
            'memristive': [
                {'label': 'ID мемристора:', 'var_name': 'mem_id', 'hint': 'Например: MEM001'},
                {'label': 'Название:', 'var_name': 'mem_name', 'hint': 'Тип мемристора'},
                {'label': 'pH диапазон:', 'type': 'range', 'min_var': 'ph_min', 'max_var': 'ph_max', 'hint': '2.0 — 10.0'},
                {'label': 'Температурный диапазон (°C):', 'type': 'range', 'min_var': 't_min', 'max_var': 't_max', 'hint': '5 — 100'},
                {'label': 'Диапазон измерений (пМ):', 'type': 'range', 'min_var': 'dr_min', 'max_var': 'dr_max', 'hint': '0.0000001 — 0-1*10^11'},
                {'label': 'Модуль Юнга (ГПа):', 'var_name': 'young_modulus', 'hint': '0-1000'},
                {'label': 'Чувствительность (мВ/dec):', 'var_name': 'sensitivity', 'hint': '0-1000'},
                {'label': 'Воспроизводимость (%):', 'var_name': 'reproducibility', 'hint': '0-100'},
                {'label': 'Время отклика (с):', 'var_name': 'response_time', 'hint': '0-3600'},
                {'label': 'Стабильность (дни):', 'var_name': 'stability', 'hint': '0-365'},
                {'label': 'Предел обнаружения (нМ):', 'var_name': 'lod', 'hint': '0-1*10^5'},
                {'label': 'Долговечность (ч):', 'var_name': 'durability', 'hint': '0-8760'},
                {'label': 'Энергопотребление (мВт):', 'var_name': 'power_consumption', 'hint': '0-1000'}
            ]
        }
    
    # streamlit
    def create_menu(self):
        """Создание меню приложения для Streamlit."""
        debug("create_menu")
    
        # Создание боковой панели с меню
        st.sidebar.title("Меню")
    
        # Раздел "Файл"
        st.sidebar.subheader("📁 Файл")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("💾 Сохранить паспорт", key="menu_save_passport", width="stretch"):
                self.save_passport_to_db_streamlit()
        with col2:
            if st.button("📂 Загрузить паспорт", key="menu_load_passport", width="stretch"):
                self.load_passport_from_db_streamlit()
    
        st.sidebar.divider()

        # Раздел "Навигация"
        st.sidebar.subheader("🔀 Навигация")
        nav_col1, nav_col2, nav_col3 = st.sidebar.columns(3)
        
        with nav_col1:
            if st.button("🔬 Ввод", key="nav_data_entry", width="stretch"):
                st.session_state.active_section = 'data_entry'
                st.rerun()
        with nav_col2:
            if st.button("📊 База", key="nav_database", width="stretch"):
                st.session_state.active_section = 'database'
                st.rerun()
        with nav_col3:
            if st.button("📈 Анализ", key="nav_analysis", width="stretch"):
                st.session_state.active_section = 'analysis'
                st.rerun()
    
        # Раздел "Инструменты"
        st.sidebar.subheader("🔧 Инструменты")
        col3, col4 = st.sidebar.columns(2)
        with col3:
            debug("create_menu: col3")
            if st.button("🗑️ Очистить", key="menu_clear_form", width="stretch"):
                debug("Зажата кнопка Очистить")
                self.clear_form_streamlit()
        with col4:
            if st.button("📊 Экспорт", key="menu_export_data", width="stretch"):
                self.export_data()
    
        st.sidebar.divider()
    
        # Раздел "Справка"
        st.sidebar.subheader("❓ Справка")
        if st.button("ℹ️ О программе", key="menu_about", width="stretch"):
            st.session_state.active_section = 'about'
            st.rerun()
            
    # streamlit
    @staticmethod
    def create_data_entry_tab():
        """Создание вкладки ввода паспортов для Streamlit."""
        st.header("🔬 Ввод паспорта биосенсора v2.0")
        
        # Создаём контейнер с прокруткой (Streamlit имеет встроенную прокрутку)
        with st.container():
            # Создаём две колонки для макета
            col1, col2 = st.columns(2)
            
            # Левая колонка - Аналит и Биослой
            with col1:
                st.subheader("🎯 Целевой аналит (TA)")
                analyte_vars = {}
                analyte_vars['ta_id'] = st.text_input(
                    "ID аналита",
                    key="analyte_ta_id",
                    help="Например: TA001"
                )
                analyte_vars['ta_name'] = st.text_input(
                    "Название",
                    key="analyte_ta_name",
                    help="Полное название аналита"
                )
                col_ph_a1, col_ph_a2 = st.columns(2)
                with col_ph_a1:
                    analyte_vars['ph_min'] = st.number_input(
                        "pH минимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="analyte_ph_min",
                        help="2.0 — 10.0"
                    )
                with col_ph_a2:
                    analyte_vars['ph_max'] = st.number_input(
                        "pH максимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="analyte_ph_max",
                        help="2.0 — 10.0"
                    )
                analyte_vars['t_max'] = st.number_input(
                    "Макс. температура (°C)",
                    min_value=0,
                    max_value=180,
                    key="analyte_t_max",
                    help="0-180"
                )
                analyte_vars['stability'] = st.number_input(
                    "Стабильность (дни)",
                    min_value=0,
                    max_value=365,
                    key="analyte_stability",
                    help="0-365"
                )
                analyte_vars['half_life'] = st.number_input(
                    "Период полураспада (ч)",
                    min_value=0,
                    max_value=8760,
                    key="analyte_half_life",
                    help="0-8760"
                )
                analyte_vars['power_consumption'] = st.number_input(
                    "Энергопотребление (мВт)",
                    min_value=0,
                    max_value=1000,
                    key="analyte_power_consumption",
                    help="0-1000"
                )
                
                st.divider()
                
                st.subheader("🔴 Биораспознающий слой (BRE)")
                bio_vars = {}
                bio_vars['bre_id'] = st.text_input(
                    "ID биослоя",
                    key="bio_bre_id",
                    help="Например: BRE001"
                )
                bio_vars['bre_name'] = st.text_input(
                    "Название",
                    key="bio_bre_name",
                    help="Тип биослоя"
                )
                col_ph_b1, col_ph_b2 = st.columns(2)
                with col_ph_b1:
                    bio_vars['ph_min'] = st.number_input(
                        "pH минимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="bio_ph_min",
                        help="2.0 — 10.0"
                    )
                with col_ph_b2:
                    bio_vars['ph_max'] = st.number_input(
                        "pH максимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="bio_ph_max",
                        help="2.0 — 10.0"
                    )
                col_t_b1, col_t_b2 = st.columns(2)
                with col_t_b1:
                    bio_vars['t_min'] = st.number_input(
                        "Температура минимум (°C)",
                        min_value=4,
                        max_value=120,
                        key="bio_t_min",
                        help="4 — 120"
                    )
                with col_t_b2:
                    bio_vars['t_max'] = st.number_input(
                        "Температура максимум (°C)",
                        min_value=4,
                        max_value=120,
                        key="bio_t_max",
                        help="4 — 120"
                    )
                col_dr_b1, col_dr_b2 = st.columns(2)
                with col_dr_b1:
                    bio_vars['dr_min'] = st.number_input(
                        "Диапазон минимум (пМ)",
                        min_value=0.1,
                        max_value=1e12,
                        key="bio_dr_min",
                        help="0.1 — 1*10^12"
                    )
                with col_dr_b2:
                    bio_vars['dr_max'] = st.number_input(
                        "Диапазон максимум (пМ)",
                        min_value=0.1,
                        max_value=1e12,
                        key="bio_dr_max",
                        help="0.1 — 1*10^12"
                    )
                bio_vars['sensitivity'] = st.number_input(
                    "Чувствительность (мкА/(мкМ*см²))",
                    min_value=0.0,
                    max_value=20000.0,
                    key="bio_sensitivity",
                    help="0.01 — 1000"
                )
                bio_vars['reproducibility'] = st.number_input(
                    "Воспроизводимость (%)",
                    min_value=0,
                    max_value=100,
                    key="bio_reproducibility",
                    help="0-100"
                )
                bio_vars['response_time'] = st.number_input(
                    "Время отклика (с)",
                    min_value=0,
                    max_value=3600,
                    key="bio_response_time",
                    help="0-3600"
                )
                bio_vars['stability'] = st.number_input(
                    "Стабильность (дни)",
                    min_value=0,
                    max_value=365,
                    key="bio_stability",
                    help="0-365"
                )
                bio_vars['lod'] = st.number_input(
                    "Предел обнаружения (нМ)",
                    min_value=0,
                    max_value=100000,
                    key="bio_lod",
                    help="0-100000"
                )
                bio_vars['durability'] = st.number_input(
                    "Долговечность (ч)",
                    min_value=0,
                    max_value=100000,
                    key="bio_durability",
                    help="0-100000"
                )
                bio_vars['power_consumption'] = st.number_input(
                    "Энергопотребление (мВт)",
                    min_value=0,
                    max_value=1000,
                    key="bio_power_consumption",
                    help="0-1000"
                )
            
            # Правая колонка - Иммобилизация и Мемристор
            with col2:
                st.subheader("🟡 Иммобилизационный слой (IM)")
                immob_vars = {}
                immob_vars['im_id'] = st.text_input(
                    "ID иммобилизации",
                    key="immob_im_id",
                    help="Например: IM001"
                )
                immob_vars['im_name'] = st.text_input(
                    "Название",
                    key="immob_im_name",
                    help="Тип иммобилизации"
                )
                col_ph_i1, col_ph_i2 = st.columns(2)
                with col_ph_i1:
                    immob_vars['ph_min'] = st.number_input(
                        "pH минимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="immob_ph_min",
                        help="2.0 — 10.0"
                    )
                with col_ph_i2:
                    immob_vars['ph_max'] = st.number_input(
                        "pH максимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="immob_ph_max",
                        help="2.0 — 10.0"
                    )
                col_t_i1, col_t_i2 = st.columns(2)
                with col_t_i1:
                    immob_vars['t_min'] = st.number_input(
                        "Температура минимум (°C)",
                        min_value=4,
                        max_value=120,
                        key="immob_t_min",
                        help="4 — 95"
                    )
                with col_t_i2:
                    immob_vars['t_max'] = st.number_input(
                        "Температура максимум (°C)",
                        min_value=4,
                        max_value=120,
                        key="immob_t_max",
                        help="4 — 95"
                    )
                immob_vars['young_modulus'] = st.number_input(
                    "Модуль Юнга (ГПа)",
                    min_value=0,
                    max_value=1000,
                    key="immob_young_modulus",
                    help="0-1000"
                )
                immob_vars['adhesion'] = st.selectbox(
                    "Адгезия",
                    ["низкая", "средняя", "высокая"],
                    key="immob_adhesion",
                    help="Уровень адгезии"
                )
                immob_vars['solubility'] = st.selectbox(
                    "Растворимость",
                    ["низкая", "средняя", "высокая"],
                    key="immob_solubility",
                    help="Уровень растворимости"
                )
                immob_vars['loss_coefficient'] = st.number_input(
                    "Коэффициент потерь",
                    min_value=0.0,
                    max_value=1.0,
                    key="immob_loss_coefficient",
                    help="0-1"
                )
                immob_vars['reproducibility'] = st.number_input(
                    "Воспроизводимость (%)",
                    min_value=0,
                    max_value=100,
                    key="immob_reproducibility",
                    help="0-100"
                )
                immob_vars['response_time'] = st.number_input(
                    "Время отклика (с)",
                    min_value=0,
                    max_value=3600,
                    key="immob_response_time",
                    help="0-3600"
                )
                immob_vars['stability'] = st.number_input(
                    "Стабильность (дни)",
                    min_value=0,
                    max_value=365,
                    key="immob_stability",
                    help="0-365"
                )
                immob_vars['durability'] = st.number_input(
                    "Долговечность (ч)",
                    min_value=0,
                    max_value=8760,
                    key="immob_durability",
                    help="0-8760"
                )
                immob_vars['power_consumption'] = st.number_input(
                    "Энергопотребление (мВт)",
                    min_value=0,
                    max_value=1000,
                    key="immob_power_consumption",
                    help="0-1000"
                )
                
                st.divider()
                
                st.subheader("🟣 Мемристивный слой (MEM)")
                mem_vars = {}
                mem_vars['mem_id'] = st.text_input(
                    "ID мемристора",
                    key="mem_mem_id",
                    help="Например: MEM001"
                )
                mem_vars['mem_name'] = st.text_input(
                    "Название",
                    key="mem_mem_name",
                    help="Тип мемристора"
                )
                col_ph_m1, col_ph_m2 = st.columns(2)
                with col_ph_m1:
                    mem_vars['ph_min'] = st.number_input(
                        "pH минимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="mem_ph_min",
                        help="2.0 — 10.0"
                    )
                with col_ph_m2:
                    mem_vars['ph_max'] = st.number_input(
                        "pH максимум",
                        min_value=2.0,
                        max_value=10.0,
                        key="mem_ph_max",
                        help="2.0 — 10.0"
                    )
                col_t_m1, col_t_m2 = st.columns(2)
                with col_t_m1:
                    mem_vars['t_min'] = st.number_input(
                        "Температура минимум (°C)",
                        min_value=5,
                        max_value=120,
                        key="mem_t_min",
                        help="5 — 100"
                    )
                with col_t_m2:
                    mem_vars['t_max'] = st.number_input(
                        "Температура максимум (°C)",
                        min_value=5,
                        max_value=120,
                        key="mem_t_max",
                        help="5 — 100"
                    )
                col_dr_m1, col_dr_m2 = st.columns(2)
                with col_dr_m1:
                    mem_vars['dr_min'] = st.number_input(
                        "Диапазон минимум (пМ)",
                        min_value=1e-7,
                        max_value=1e11,
                        key="mem_dr_min",
                        help="0.0000001 — 1*10^11"
                    )
                with col_dr_m2:
                    mem_vars['dr_max'] = st.number_input(
                        "Диапазон максимум (пМ)",
                        min_value=1e-7,
                        max_value=1e11,
                        key="mem_dr_max",
                        help="0.0000001 — 1*10^11"
                    )
                mem_vars['young_modulus'] = st.number_input(
                    "Модуль Юнга (ГПа)",
                    min_value=0,
                    max_value=1000,
                    key="mem_young_modulus",
                    help="0-1000"
                )
                mem_vars['sensitivity'] = st.number_input(
                    "Чувствительность (мВ/dec)",
                    min_value=0.0,
                    max_value=1000.0,
                    key="mem_sensitivity",
                    help="0-1000"
                )
                mem_vars['reproducibility'] = st.number_input(
                    "Воспроизводимость (%)",
                    min_value=0,
                    max_value=100,
                    key="mem_reproducibility",
                    help="0-100"
                )
                mem_vars['response_time'] = st.number_input(
                    "Время отклика (с)",
                    min_value=0,
                    max_value=3600,
                    key="mem_response_time",
                    help="0-3600"
                )
                mem_vars['stability'] = st.number_input(
                    "Стабильность (дни)",
                    min_value=0,
                    max_value=365,
                    key="mem_stability",
                    help="0-365"
                )
                mem_vars['lod'] = st.number_input(
                    "Предел обнаружения (нМ)",
                    min_value=0,
                    max_value=100000,
                    key="mem_lod",
                    help="0-1*10^5"
                )
                mem_vars['durability'] = st.number_input(
                    "Долговечность (ч)",
                    min_value=0,
                    max_value=100000,
                    key="mem_durability",
                    help="0-8760"
                )
                mem_vars['power_consumption'] = st.number_input(
                    "Энергопотребление (мВт)",
                    min_value=0,
                    max_value=1000,
                    key="mem_power_consumption",
                    help="0-1000"
                )
        
        # Кнопки управления в нижней части
        st.divider()
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("💾 Сохранить паспорт", key="save_btn", width="stretch"):
                st.info("✅ Паспорт сохранён в базу данных")
        with btn_col2:
            if st.button("🗑️ Очистить форму", key="clear_btn", width="stretch"):
                st.info("✅ Форма очищена")
        with btn_col3:
            if st.button("📁 Загрузить паспорт", key="load_btn", width="stretch"):
                st.info("✅ Паспорт загружен из БД")   

    # streamlit
    def create_database_tab(self):
        """Создание вкладки базы данных для Streamlit."""
        st.header("📊 База данных биосенсоров")
        
        # Кнопки для выбора типа данных
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("🎯 TA (аналиты)", width="stretch"):
                st.session_state.current_data_type = 'analytes'
                st.session_state.current_page = 0
        with col2:
            if st.button("🔴 BRE (биослои)", width="stretch"):
                st.session_state.current_data_type = 'bio_layers'
                st.session_state.current_page = 0
        with col3:
            if st.button("🟡 IM (иммобилизация)", width="stretch"):
                st.session_state.current_data_type = 'immobilization_layers'
                st.session_state.current_page = 0
        with col4:
            if st.button("🟣 MEM (мемристоры)", width="stretch"):
                st.session_state.current_data_type = 'memristive_layers'
                st.session_state.current_page = 0
        with col5:
            if st.button("🔄 Обновить", width="stretch"):
                st.rerun()
        
        st.divider()
        
        # Пагинация
        page_size = st.number_input("Записей на странице:", min_value=5, max_value=100, value=20)
        current_page = st.session_state.get('current_page', 0)
        current_data_type = st.session_state.get('current_data_type', 'analytes')
        
        # Получение данных в зависимости от типа
        offset = current_page * page_size
        
        if current_data_type == 'analytes':
            data = self.db_manager.list_all_analytes_paginated(page_size, offset)
            columns = ["TA_ID", "TA_Name", "PH_Min", "PH_Max", "T_Max", "ST"]
            title = "📋 Аналиты"
        elif current_data_type == 'bio_layers':
            data = self.db_manager.list_all_bio_recognition_layers_paginated(page_size, offset)
            columns = ["BRE_ID", "BRE_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "SN"]
            title = "🔴 Биораспознающие слои"
        elif current_data_type == 'immobilization_layers':
            data = self.db_manager.list_all_immobilization_layers_paginated(page_size, offset)
            columns = ["IM_ID", "IM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "MP"]
            title = "🟡 Иммобилизационные слои"
        elif current_data_type == 'memristive_layers':
            data = self.db_manager.list_all_memristive_layers_paginated(page_size, offset)
            columns = ["MEM_ID", "MEM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "SN"]
            title = "🟣 Мемристивные слои"
        else:
            data = []
            columns = []
            title = "Данные не найдены"
        
        st.subheader(title)
        
        # Отображение таблицы
        if data:
            df = __import__('pandas').DataFrame(data)
            st.dataframe(df, width="stretch")
        else:
            st.info("Нет данных для отображения на этой странице.")
        
        # Навигация по страницам
        st.divider()
        col_prev, col_page, col_next = st.columns(3)
        
        with col_prev:
            if st.button("◀ Предыдущая", width="stretch", disabled=(current_page == 0)):
                st.session_state.current_page = max(0, current_page - 1)
                st.rerun()
        
        with col_page:
            st.write(f"**Страница {current_page + 1}**", unsafe_allow_html=True)
        
        with col_next:
            if st.button("Следующая ▶", width="stretch", disabled=(len(data) < page_size)):
                st.session_state.current_page = current_page + 1
                st.rerun()
    
    # streamlit
    def create_analysis_tab(self):
        """Создание вкладки анализа для Streamlit."""
        st.header("📈 Анализ характеристик")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏆 Лучшие комбинации", width="stretch"):
                self.sythesize_sensor_combinations()
                self.show_best_combinations()
        
        with col2:
            if st.button("📊 Сравнительный анализ", width="stretch"):
                self.comparative_analysis()
        
        with col3:
            if st.button("📈 Статистика", width="stretch"):
                self.show_statistics()
        
        st.divider()
        
        # Область для вывода результатов анализа
        st.session_state.setdefault('analysis_result', "Выберите тип анализа...")
        st.text_area(
            "Результаты анализа:",
            value=st.session_state.get('analysis_result', ''),
            height=300,
            disabled=True
        )
    
    # streamlit
    def save_passport_to_db_streamlit(self):
        """Сохранение паспорта в БД из Streamlit-форм."""
        try:
            # Сохранение аналита
            analyte_data = {
                'TA_ID': st.session_state.get('analyte_ta_id', '', cache=False),
                'TA_Name': st.session_state.get('analyte_ta_name', ''),
                'PH_Min': st.session_state.get('analyte_ph_min'),
                'PH_Max': st.session_state.get('analyte_ph_max'),
                'T_Max': st.session_state.get('analyte_t_max'),
                'ST': st.session_state.get('analyte_stability'),
                'HL': st.session_state.get('analyte_half_life'),
                'PC': st.session_state.get('analyte_power_consumption')
            }
            
            '''if analyte_data['TA_ID']:
                if self.db_manager.insert_analyte(analyte_data):
                    st.success("✅ Аналит сохранён")
                    self.logger.info(f"Аналит {analyte_data['TA_ID']} сохранён")
            '''
            if not analyte_data['TA_ID']:
                st.error("❌ ID аналита не может быть пустым")
                return
            
            result = self.db_manager.insert_analyte(analyte_data)
            
            # Обработка результата в GUI слое
            if result == "DUPLICATE":
                st.warning(f"⚠️ Аналит {analyte_data['TA_ID']} уже существует")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Перезаписать", key=f"overwrite_analyte_{analyte_data['TA_ID']}"):
                        # Удалить существующий и вставить новый
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM Analytes WHERE TA_ID = ?", (analyte_data['TA_ID'],))
                            conn.commit()
                        self.db_manager.insert_analyte(analyte_data)
                        st.success("✅ Аналит перезаписан!")
                with col2:
                    if st.button("❌ Отмена", key=f"cancel_analyte_{analyte_data['TA_ID']}"):
                        st.info("Операция отменена")
            elif result is True:
                st.success(f"✅ Аналит {analyte_data['TA_ID']} успешно сохранён")
            else:
                st.error(f"❌ Ошибка сохранения аналита")
            
            # Сохранение биораспознающего слоя
            bio_data = {
                'BRE_ID': st.session_state.get('bio_bre_id', ''),
                'BRE_Name': st.session_state.get('bio_bre_name', ''),
                'PH_Min': st.session_state.get('bio_ph_min'),
                'PH_Max': st.session_state.get('bio_ph_max'),
                'T_Min': st.session_state.get('bio_t_min'),
                'T_Max': st.session_state.get('bio_t_max'),
                'SN': st.session_state.get('bio_sensitivity'),
                'DR_Min': st.session_state.get('bio_dr_min'),
                'DR_Max': st.session_state.get('bio_dr_max'),
                'RP': st.session_state.get('bio_reproducibility'),
                'TR': st.session_state.get('bio_response_time'),
                'ST': st.session_state.get('bio_stability'),
                'LOD': st.session_state.get('bio_lod'),
                'HL': st.session_state.get('bio_durability'),
                'PC': st.session_state.get('bio_power_consumption')
            }

            if not bio_data["BRE_ID"]:
                st.error("❌ Введите BRE_ID")
                return

            result = self.db_manager.insert_bio_recognition_layer(bio_data)

            # Обработка результата в GUI слое
            if result == "DUPLICATE":
                st.warning(f"⚠️ Биослой {bio_data['BRE_ID']} уже существует")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ Перезаписать", key=f"overwrite_bio_ui_{bio_data['BRE_ID']}"):
                        try:
                            # Удаляем существующую запись и пробуем вставить снова
                            with get_connection() as conn:
                                cur = conn.cursor()
                                cur.execute("DELETE FROM BioRecognitionLayers WHERE BRE_ID = ?", (bio_data['BRE_ID'],))
                                conn.commit()
                            inserted = self.db_manager.insert_bio_recognition_layer(bio_data)
                            if inserted is True:
                                st.success("✅ Биослой перезаписан")
                            else:
                                st.error("❌ Ошибка при перезаписи биослоя")
                            st.rerun()
                        except Exception as e:
                            self.logger.exception("Ошибка перезаписи биослоя")
                            st.error(f"❌ Ошибка: {e}")
                with col2:
                    if st.button("❌ Отмена", key=f"cancel_bio_ui_{bio_data['BRE_ID']}"):
                        st.info("Операция отменена")
                return

            if result is True:
                st.success("✅ Биослой сохранён")
                st.rerun()
            else:
                st.error("❌ Не удалось сохранить биослой")
                
            # Сохранение иммобилизационного слоя
            immob_data = {
                'IM_ID': st.session_state.get('immob_im_id', ''),
                'IM_Name': st.session_state.get('immob_im_name', ''),
                'PH_Min': st.session_state.get('immob_ph_min'),
                'PH_Max': st.session_state.get('immob_ph_max'),
                'T_Min': st.session_state.get('immob_t_min'),
                'T_Max': st.session_state.get('immob_t_max'),
                'MP': st.session_state.get('immob_young_modulus'),
                'Adh': st.session_state.get('immob_adhesion', ''),
                'Sol': st.session_state.get('immob_solubility', ''),
                'K_IM': st.session_state.get('immob_loss_coefficient'),
                'RP': st.session_state.get('immob_reproducibility'),
                'TR': st.session_state.get('immob_response_time'),
                'ST': st.session_state.get('immob_stability'),
                'HL': st.session_state.get('immob_durability'),
                'PC': st.session_state.get('immob_power_consumption')
            }

            # Обработка результата в GUI слое
            if immob_data['IM_ID']:
                result = self.db_manager.insert_immobilization_layer(immob_data)

                if result == "DUPLICATE":
                    st.warning(f"⚠️ Иммобилизационный слой {immob_data['IM_ID']} уже существует")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("✅ Перезаписать", key=f"overwrite_immob_ui_{immob_data['IM_ID']}"):
                            try:
                                with get_connection() as conn:
                                    cur = conn.cursor()
                                    cur.execute("DELETE FROM ImmobilizationLayers WHERE IM_ID = ?", (immob_data['IM_ID'],))
                                    conn.commit()
                                inserted = self.db_manager.insert_immobilization_layer(immob_data)
                                if inserted is True:
                                    st.success("✅ Иммобилизационный слой перезаписан")
                                else:
                                    st.error("❌ Ошибка при перезаписи иммобилизационного слоя")
                                st.rerun()
                            except Exception as e:
                                self.logger.exception("Ошибка перезаписи иммобилизационного слоя")
                                st.error(f"❌ Ошибка: {e}")
                    with col2:
                        if st.button("❌ Отмена", key=f"cancel_immob_ui_{immob_data['IM_ID']}"):
                            st.info("Операция отменена")
                elif result is True:
                    st.success("✅ Иммобилизационный слой сохранён")
                    self.logger.info(f"Иммобилизационный слой {immob_data['IM_ID']} сохранён")
                else:
                    st.error("❌ Не удалось сохранить иммобилизационный слой")

            # Сохранение мемристивного слоя
            mem_data = {
                'MEM_ID': st.session_state.get('mem_mem_id', ''),
                'MEM_Name': st.session_state.get('mem_mem_name', ''),
                'PH_Min': st.session_state.get('mem_ph_min'),
                'PH_Max': st.session_state.get('mem_ph_max'),
                'T_Min': st.session_state.get('mem_t_min'),
                'T_Max': st.session_state.get('mem_t_max'),
                'MP': st.session_state.get('mem_young_modulus'),
                'SN': st.session_state.get('mem_sensitivity'),
                'DR_Min': st.session_state.get('mem_dr_min'),
                'DR_Max': st.session_state.get('mem_dr_max'),
                'RP': st.session_state.get('mem_reproducibility'),
                'TR': st.session_state.get('mem_response_time'),
                'ST': st.session_state.get('mem_stability'),
                'LOD': st.session_state.get('mem_lod'),
                'HL': st.session_state.get('mem_durability'),
                'PC': st.session_state.get('mem_power_consumption')
            }

            if not mem_data['MEM_ID']:
                st.error("❌ ID мемристора не может быть пустым")
                return
            
            result = self.db_manager.insert_memristive_layer(mem_data)
            
            # Обработка результата в GUI слое
            if result == "DUPLICATE":
                st.warning(f"⚠️ Мемристивный слой {mem_data['MEM_ID']} уже существует")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ Перезаписать", key=f"overwrite_mem_ui_{mem_data['MEM_ID']}"):
                        try:
                            with get_connection() as conn:
                                cur = conn.cursor()
                                cur.execute("DELETE FROM MemristiveLayers WHERE MEM_ID = ?", (mem_data['MEM_ID'],))
                                conn.commit()
                            inserted = self.db_manager.insert_memristive_layer(mem_data)
                            if inserted is True:
                                st.success("✅ Мемристивный слой перезаписан")
                            else:
                                st.error("❌ Ошибка при перезаписи мемристивного слоя")
                            st.rerun()
                        except Exception as e:
                            self.logger.exception("Ошибка перезаписи мемристивного слоя")
                            st.error(f"❌ Ошибка: {e}")
                with col2:
                    if st.button("❌ Отмена", key=f"cancel_mem_ui_{mem_data['MEM_ID']}"):
                        st.info("Операция отменена")
            elif result is True:
                st.success("✅ Мемристивный слой сохранён")
                self.logger.info(f"Мемристивный слой {mem_data['MEM_ID']} сохранён")
            else:
                st.error("❌ Не удалось сохранить мемристивный слой")

            st.success("✅ Все паспорты успешно сохранены!")

            """Сохранение комбинации сенсора с Streamlit UI и обработкой дубликатов."""
            combo_data = {
                'Combo_ID': st.session_state.get('combo_id', ''),
                'TA_ID': st.session_state.get('combo_ta_id', ''),
                'BRE_ID': st.session_state.get('combo_bre_id', ''),
                'IM_ID': st.session_state.get('combo_im_id', ''),
                'MEM_ID': st.session_state.get('combo_mem_id', ''),
                'SN_total': st.session_state.get('combo_sn_total'),
                'TR_total': st.session_state.get('combo_tr_total'),
                'ST_total': st.session_state.get('combo_st_total'),
                'RP_total': st.session_state.get('combo_rp_total'),
                'LOD_total': st.session_state.get('combo_lod_total'),
                'DR_total': st.session_state.get('combo_dr_total', ''),
                'HL_total': st.session_state.get('combo_hl_total'),
                'PC_total': st.session_state.get('combo_pc_total'),
                'Score': st.session_state.get('combo_score'),
                'created_at': st.session_state.get('combo_created_at')
            }
            
            if not combo_data['Combo_ID']:
                st.error("❌ ID комбинации не может быть пустым")
                return
            
            result = self.db_manager.insert_sensor_combination(combo_data)
            
            # Обработка результата в GUI слое
            if result == "DUPLICATE":
                st.warning(f"⚠️ Комбинация {combo_data['Combo_ID']} уже существует")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ Перезаписать", key=f"overwrite_combo_ui_{combo_data['Combo_ID']}"):
                        try:
                            with get_connection() as conn:
                                cur = conn.cursor()
                                cur.execute("DELETE FROM SensorCombinations WHERE Combo_ID = ?", (combo_data['Combo_ID'],))
                                conn.commit()
                            inserted = self.db_manager.insert_sensor_combination(combo_data)
                            if inserted is True:
                                st.success("✅ Комбинация сенсора перезаписана")
                            else:
                                st.error("❌ Ошибка при перезаписи комбинации сенсора")
                            st.rerun()
                        except Exception as e:
                            self.logger.exception("Ошибка перезаписи комбинации сенсора")
                            st.error(f"❌ Ошибка: {e}")
                with col2:
                    if st.button("❌ Отмена", key=f"cancel_combo_ui_{combo_data['Combo_ID']}"):
                        st.info("Операция отменена")
            elif result is True:
                st.success("✅ Комбинация сенсора сохранена")
                self.logger.info(f"Комбинация сенсора {combo_data['Combo_ID']} сохранена")
            else:
                st.error("❌ Не удалось сохранить комбинацию сенсора")
                    
        except Exception as e:
            st.error(f"❌ Ошибка сохранения: {str(e)}")
            self.logger.error(f"Ошибка сохранения паспортов: {e}")

    def normolize(self, value, kind=None):
        """Нормализация значения в диапазоне 0-1 в зависимости от типа характеристики."""
        if value == None:
            return 0.0
        # if (kind == 'SN' or kind == 'LOD'):
        result = math.log(10, value)
        return result

    # Рассмотрение всех паспортов базы данных и создание комбинаций сенсоров
    def sythesize_sensor_combinations(self):
        """Синтез комбинаций сенсоров на основе всех паспортов в базе данных."""
        analytes = self.db_manager.list_all_analytes()
        bio_layers = self.db_manager.list_all_bio_recognition_layers()
        immob_layers = self.db_manager.list_all_immobilization_layers()
        mem_layers = self.db_manager.list_all_memristive_layers()

        total_combinations = 0
        successful_combinations = 0

        for analyte in analytes:
            for bio_layer in bio_layers:
                for immob_layer in immob_layers:
                    for mem_layer in mem_layers:
                        total_combinations += 1
                        try:
                            result = self.create_sensor_combination(
                                analyte['TA_ID'],
                                bio_layer['BRE_ID'],
                                immob_layer['IM_ID'],
                                mem_layer['MEM_ID']
                            )
                            if result == True:
                                successful_combinations += 1
                        except Exception as e:
                            self.logger.error(f"Ошибка при создании комбинации: {e}")

        self.logger.info(f"Всего комбинаций: {total_combinations}, Успешных: {successful_combinations}")
        
    def create_sensor_combination(self, analyte_id, bio_id, immob_id, mem_id):
        """Создание комбинаций сенсоров на основе пересечения диапазонов pH и температур."""

        # Установка диапазонов для условий совместимости
        MP_ADD = 0.5  # ГПа

        ADH_MIN = "Низкая"
        ADH_MAX = "Высокая"

        SOL_MIN = "Низкая"
        SOL_MAX = "Высокая"

        try:
            # Загрузка одного паспорта каждого типа
            analyte = self.db_manager.get_analyte_by_id(analyte_id)  # Укажите ID аналита
            bio_layer = self.db_manager.get_bio_recognition_layer_by_id(bio_id)  # Укажите ID биослоя
            immob_layer = self.db_manager.get_immobilization_layer_by_id(immob_id)  # Укажите ID иммобилизации
            mem_layer = self.db_manager.get_memristive_layer_by_id(mem_id)  # Укажите ID мемристора

            # Проверка наличия всех данных
            if not (analyte and bio_layer and immob_layer and mem_layer):
                self.logger.info("❌ Не удалось загрузить все слои. Проверьте наличие данных в базе.")
                return

            # Извлечение диапазонов pH
            analyte_ph_min, analyte_ph_max = analyte['PH_Min'], analyte['PH_Max']
            bio_ph_min, bio_ph_max = bio_layer['PH_Min'], bio_layer['PH_Max']
            immob_ph_min, immob_ph_max = immob_layer['PH_Min'], immob_layer['PH_Max']
            mem_ph_min, mem_ph_max = mem_layer['PH_Min'], mem_layer['PH_Max']

            # Извлечение температур
            analyte_t_max = analyte['T_Max']
            bio_t_max = bio_layer['T_Max']
            immob_t_max = immob_layer['T_Max']
            mem_t_max = mem_layer['T_Max']

            bio_t_min = bio_layer['T_Min']
            immob_t_min = immob_layer['T_Min']
            mem_t_min = mem_layer['T_Min']

            # Извлечение механической совместимости
            immob_mp = immob_layer['MP']
            mem_mp = mem_layer['MP']

            # Извлечение адгезии и растворимости
            immob_adh = immob_layer['Adh']
            immob_sol = immob_layer['Sol']

            # Проверка пересечения диапазонов pH
            if not (analyte_ph_min <= bio_ph_max and analyte_ph_max >= bio_ph_min and
                    analyte_ph_min <= immob_ph_max and analyte_ph_max >= immob_ph_min and
                    analyte_ph_min <= mem_ph_max and analyte_ph_max >= mem_ph_min):
                self.logger.info("ℹ️ Диапазоны pH не пересекаются. Комбинация не создана.")
                return

            # Проверка температурной устойчивости аналита
            if not (bio_t_max <= analyte_t_max and immob_t_max <= analyte_t_max and mem_t_max <= analyte_t_max):
                self.logger.info("ℹ️ Температура одного из слоёв превышает температуру аналита. Комбинация не создана.")
                return
            
            # Проверка температурной совместимости слоев
            if not (mem_t_min <= bio_t_min and bio_t_max <= mem_t_max and 
                    mem_t_min <= immob_t_min and immob_t_max <= mem_t_max):
                 self.logger.info("ℹ️ Рабочие температурные диапозоны слоев не допустимы для слоя MEM. Комбинация не создана.")

            '''
            # Проверка механической совместимости слоев
            if not (immob_mp - mem_mp < MP_ADD):
                self.logger.info("ℹ️ Модуль Юнга иммобилизационного слоя превышает модуль мемристивного слоя. Комбинация не создана.")
                return
            
            # Проверка адгезии
            if not (ADH_MIN <= immob_adh <= ADH_MAX):
                self.logger.info("ℹ️ Адгезия иммобилизационного слоя вне допустимого диапазона. Комбинация не создана.")
                return
            
            # Проверка растворимости
            if not (SOL_MIN <= immob_sol <= SOL_MAX):
                self.logger.info("ℹ️ Растворимость иммобилизационного слоя вне допустимого диапазона. Комбинация не создана.")
                return
            '''

            # РАСЧЕТ ИНТЕГРАЛЬНЫХ ХАРАКТЕРИСТИКИ

            # Чувствительность (SN_total)
            # Извлечение значений чувствительности
            bio_sn = bio_layer['SN']
            mem_sn = mem_layer['SN']
            K_IM = immob_layer['K_IM']

            # Расчёт итоговой чувствительности
            SN_total = bio_sn * mem_sn * K_IM
            SN_total_norm = self.normolize(SN_total, kind='SN')
            w_SN_total_norm = 1 # коэффициент веса (важности) для чувствительности

            # Время отклика (TR_total)
            bio_tr = bio_layer['TR']
            immob_tr = immob_layer['TR']
            mem_tr = mem_layer['TR']

            # Расчёт итогового времени отклика
            TR_total = bio_tr + immob_tr + mem_tr
            TR_total_norm = self.normolize(TR_total, kind='TR')
            w_TR_total_norm = 1  # коэффициент веса (важности) для времени отклика

            # Стабильность (ST_total)
            bio_st = bio_layer['ST']
            immob_st = immob_layer['ST']
            mem_st = mem_layer['ST']

            # Расчёт итоговой стабильности
            ST_total = min(bio_st, immob_st, mem_st)
            ST_total_norm = self.normolize(ST_total, kind='ST')
            w_ST_total_norm = 1  # коэффициент веса (важности) для стабильности

            # Воспроизводимость (RP_total)
            bio_rp = bio_layer['RP']
            immob_rp = immob_layer['RP']
            mem_rp = mem_layer['RP']

            # Расчёт итоговой воспроизводимости
            RP_total = min(bio_rp, immob_rp, mem_rp)
            RP_total_norm = self.normolize(RP_total, kind='RP')
            w_RP_total_norm = 1  # коэффициент веса (важности) для воспроизводимости

            # Предел обнаружения (LOD_total)
            bio_lod = bio_layer['LOD']
            mem_lod = mem_layer['LOD']

            # Расчёт итогового предела обнаружения
            LOD_total = max(bio_lod, mem_lod)
            LOD_total_norm = self.normolize(LOD_total, kind='LOD')
            w_LOD_total_norm = 1  # коэффициент веса (важности) для предела обнаружения

            # Диапазон (DR_total)
            bio_dr_min = bio_layer['DR_Min']
            bio_dr_max = bio_layer['DR_Max']
            mem_dr_min = mem_layer['DR_Min']
            mem_dr_max = mem_layer['DR_Max']

            # Расчёт итогового диапазона
            DR_total = (min(bio_dr_max, mem_dr_max) - max(bio_dr_min, mem_dr_min)) # Поиск пересечения диапазонов
            DR_total_norm = self.normolize(DR_total, kind='DR')
            w_DR_total_norm = 1  # коэффициент веса (важности) для диапазона

            # Долговечность (HL)
            bio_hl = bio_layer['HL']
            immob_hl = immob_layer['HL']
            mem_hl = mem_layer['HL']

            # Расчёт итоговой долговечности
            HL_total = min(bio_hl, immob_hl, mem_hl)
            HL_total_norm = self.normolize(HL_total, kind='HL')
            w_HL_total_norm = 1  # коэффициент веса (важности) для долговечности

            # Энергопотребление (PC_total)
            bio_pc = bio_layer['PC']
            immob_pc = immob_layer['PC']
            mem_pc = mem_layer['PC']

            # Расчёт итогового энергопотребления
            PC_total = bio_pc + immob_pc + mem_pc
            PC_total_norm = self.normolize(PC_total, kind='PC')
            w_PC_total_norm = 1  # коэффициент веса (важности) для энергопотребления

            # Расчет коэффициента достоверности
            alfa = 0.3 # штраф за неполноту данных
            ro = 1 # доля известных параметров
            С = 1 - alfa * (1 - ro) # коэффициент достоверности

            # Расчет итогового балла (Score)
            Score = (SN_total_norm * w_SN_total_norm +
                     TR_total_norm * w_TR_total_norm +  # Чем меньше время отклика, тем лучше
                     ST_total_norm * w_ST_total_norm +
                     RP_total_norm * w_RP_total_norm +
                     LOD_total_norm * w_LOD_total_norm +  # Чем меньше LOD, тем лучше
                     DR_total_norm * w_DR_total_norm +
                     HL_total_norm * w_HL_total_norm +
                     PC_total_norm * w_PC_total_norm) / С  # Чем меньше энергопотребление, тем лучше

            # Создание идентификатора комбинации
            Combo_ID = f"COMBO_{analyte['TA_ID']}_{bio_layer['BRE_ID']}_{immob_layer['IM_ID']}_{mem_layer['MEM_ID']}"

            '''
            # Проверка на существование комбинации
            existing_combo = self.db_manager.get_sensor_combination_by_id(Combo_ID)
            if existing_combo:
                self.logger.info(f"ℹ️ Комбинация {Combo_ID} уже существует в базе данных.")
                return
            '''
        
            # Если все проверки пройдены, создаём комбинацию
            combination_data = {
                'Combo_ID': Combo_ID,  # Уникальный ID комбинации
                'TA_ID': analyte['TA_ID'],
                'BRE_ID': bio_layer['BRE_ID'],
                'IM_ID': immob_layer['IM_ID'],
                'MEM_ID': mem_layer['MEM_ID'],
                'SN_total': SN_total,  # Здесь можно рассчитать итоговые значения
                'TR_total': TR_total,
                'ST_total': ST_total,
                'RP_total': RP_total,
                'LOD_total': LOD_total,
                'DR_total': DR_total,
                'HL_total': HL_total,
                'PC_total': PC_total,
                'Score': Score,  # Здесь можно рассчитать итоговый балл
                'created_at': None  # Автоматически заполняется в БД
            }

            # Добавление комбинации в базу данных
            result = self.db_manager.insert_sensor_combination(combination_data)
            if result == "DUPLICATE":
                self.logger.info(f"⚠️ Комбинация {combination_data['Combo_ID']} уже существует.")
            elif result:
                self.logger.info(f"✅ Комбинация {combination_data['Combo_ID']} успешно добавлена в базу данных.")
                return True
            else:
                self.logger.info("❌ Ошибка добавления комбинации в базу данных.")
        except Exception as e:
            # st.error(f"❌ Ошибка при создании комбинации: {str(e)}")
            self.logger.error(f"Ошибка при создании комбинации: {e}")

    # streamlit
    @staticmethod
    def clear_form_streamlit():
        """Очистка формы (перезагрузка страницы)."""
        debug("clear_form_streamlit")
        st.session_state.clear()
        st.info("✅ Форма очищена. Страница перезагружена.")
        st.rerun()
    
    def load_passport_from_db_streamlit(self):
        st.subheader("📁 Загрузить паспорт из БД")
        
        col1, col2 = st.columns(2)
        with col1:
            datatype = st.selectbox("Выберите тип слоя", ["TA", "BRE", "IM", "MEM"], key="load_datatype")
        with col2:
            layer_id = st.text_input("ID слоя", key="load_layer_id")
        
        if st.button("Загрузить", key="load_execute_btn"):
            if not layer_id:
                st.error("❌ Введите ID слоя!")
                return
            
            try:
                if datatype == "TA":
                    data = self.db_manager.get_analyte_by_id(layer_id)
                    if data:
                        # ✅ ПРАВИЛЬНЫЕ КЛЮЧИ (соответствуют key= в create_data_entry_tab)
                        st.session_state['analyte_ta_id'] = data.get('TA_ID', '')
                        st.session_state['analyte_ta_name'] = data.get('TA_Name', '')
                        st.session_state['analyte_ph_min'] = data.get('PH_Min', 0)
                        st.session_state['analyte_ph_max'] = data.get('PH_Max', 0)
                        st.session_state['analyte_t_max'] = data.get('T_Max', 0)
                        st.session_state['analyte_stability'] = data.get('ST', 0)
                        st.session_state['analyte_half_life'] = data.get('HL', 0)
                        st.session_state['analyte_power_consumption'] = data.get('PC', 0)
                        
                        st.success(f"✅ Паспорт TA '{data.get('TA_Name', 'Без названия')}' загружен!")
                    else:
                        st.error(f"❌ Паспорт с ID '{layer_id}' не найден")
                        
                elif datatype == "BRE":
                    data = self.db_manager.get_bio_recognition_layer_by_id(layer_id)
                    if data:
                        st.session_state['bio_bre_id'] = data.get('BRE_ID', '')
                        st.session_state['bio_bre_name'] = data.get('BRE_Name', '')
                        st.session_state['bio_ph_min'] = data.get('PH_Min', 0)
                        st.session_state['bio_ph_max'] = data.get('PH_Max', 0)
                        st.session_state['bio_t_min'] = data.get('T_Min', 0)
                        st.session_state['bio_t_max'] = data.get('T_Max', 0)
                        st.session_state['bio_sensitivity'] = data.get('SN', 0)
                        st.session_state['bio_dr_min'] = data.get('DR_Min', 0)
                        st.session_state['bio_dr_max'] = data.get('DR_Max', 0)
                        st.session_state['bio_reproducibility'] = data.get('RP', 0)
                        st.session_state['bio_response_time'] = data.get('TR', 0)
                        st.session_state['bio_stability'] = data.get('ST', 0)
                        st.session_state['bio_lod'] = data.get('LOD', 0)
                        st.session_state['bio_durability'] = data.get('HL', 0)
                        st.session_state['bio_power_consumption'] = data.get('PC', 0)
                        
                        st.success(f"✅ Паспорт BRE '{data.get('BRE_Name', 'Без названия')}' загружен!")
                    else:
                        st.error(f"❌ Паспорт с ID '{layer_id}' не найден")
                        
                elif datatype == "IM":
                    data = self.db_manager.get_immobilization_layer_by_id(layer_id)
                    if data:
                        st.session_state['immob_im_id'] = data.get('IM_ID', '')
                        st.session_state['immob_im_name'] = data.get('IM_Name', '')
                        st.session_state['immob_ph_min'] = data.get('PH_Min', 0)
                        st.session_state['immob_ph_max'] = data.get('PH_Max', 0)
                        st.session_state['immob_t_min'] = data.get('T_Min', 0)
                        st.session_state['immob_t_max'] = data.get('T_Max', 0)
                        st.session_state['immob_young_modulus'] = data.get('MP', 0)
                        st.session_state['immob_adhesion'] = data.get('Adh', 'средняя')
                        st.session_state['immob_solubility'] = data.get('Sol', 'средняя')
                        st.session_state['immob_loss_coefficient'] = data.get('K_IM', 0)
                        st.session_state['immob_reproducibility'] = data.get('RP', 0)
                        st.session_state['immob_response_time'] = data.get('TR', 0)
                        st.session_state['immob_stability'] = data.get('ST', 0)
                        st.session_state['immob_durability'] = data.get('HL', 0)
                        st.session_state['immob_power_consumption'] = data.get('PC', 0)
                        
                        st.success(f"✅ Паспорт IM '{data.get('IM_Name', 'Без названия')}' загружен!")
                    else:
                        st.error(f"❌ Паспорт с ID '{layer_id}' не найден")
                        
                elif datatype == "MEM":
                    data = self.db_manager.get_memristive_layer_by_id(layer_id)
                    if data:
                        st.session_state['mem_mem_id'] = data.get('MEM_ID', '')
                        st.session_state['mem_mem_name'] = data.get('MEM_Name', '')
                        st.session_state['mem_ph_min'] = data.get('PH_Min', 0)
                        st.session_state['mem_ph_max'] = data.get('PH_Max', 0)
                        st.session_state['mem_t_min'] = data.get('T_Min', 0)
                        st.session_state['mem_t_max'] = data.get('T_Max', 0)
                        st.session_state['mem_young_modulus'] = data.get('MP', 0)
                        st.session_state['mem_sensitivity'] = data.get('SN', 0)
                        st.session_state['mem_dr_min'] = data.get('DR_Min', 0)
                        st.session_state['mem_dr_max'] = data.get('DR_Max', 0)
                        st.session_state['mem_reproducibility'] = data.get('RP', 0)
                        st.session_state['mem_response_time'] = data.get('TR', 0)
                        st.session_state['mem_stability'] = data.get('ST', 0)
                        st.session_state['mem_lod'] = data.get('LOD', 0)
                        st.session_state['mem_durability'] = data.get('HL', 0)
                        st.session_state['mem_power_consumption'] = data.get('PC', 0)
                        
                        st.success(f"✅ Паспорт MEM '{data.get('MEM_Name', 'Без названия')}' загружен!")
                    else:
                        st.error(f"❌ Паспорт с ID '{layer_id}' не найден")
                        
            except Exception as e:
                self.logger.error(f"Ошибка загрузки: {e}")
                st.error(f"❌ Ошибка при загрузке: {str(e)}")
        
        st.info("💡 После загрузки данные появятся в форме ввода. Нажмите на раздел '🔬 Ввод' в меню, чтобы увидеть загруженные значения.")

    # streamlit
    def show_analytes(self):
        """Streamlit-версия: отображение аналитов с пагинацией."""
        st.session_state['current_data_type'] = 'analytes'
        # сброс на первую страницу при явном вызове
        st.session_state.setdefault('current_page', 0)
        page_size = st.session_state.get('page_size', self.page_size)
        current_page = st.session_state.get('current_page', 0)
        offset = current_page * page_size

        analytes = self.db_manager.list_all_analytes_paginated(page_size, offset)

        st.subheader("📋 Аналиты")
        if analytes:
            df = __import__('pandas').DataFrame(analytes)
            # выводим только основные столбцы в удобном виде
            cols = [c for c in ["TA_ID", "TA_Name", "PH_Min", "PH_Max", "T_Max", "ST"] if c in df.columns]
            st.dataframe(df[cols], width="stretch")
        else:
            st.info("Нет записей аналитов для отображения.")

        # Пагинация
        st.divider()
        col_prev, col_page, col_next = st.columns([1, 1, 1])
        with col_prev:
            if st.button("◀ Предыдущая", key="analytes_prev", disabled=(current_page == 0)):
                st.session_state['current_page'] = max(0, current_page - 1)
                st.rerun()
        with col_page:
            st.markdown(f"**Страница {current_page + 1}**")
        with col_next:
            if st.button("Следующая ▶", key="analytes_next", disabled=(len(analytes) < page_size)):
                st.session_state['current_page'] = current_page + 1
                st.rerun()

    # streamlit
    def show_bio_layers(self):
        """Streamlit-версия: отображение биораспознающих слоев с пагинацией."""
        st.session_state['current_data_type'] = 'bio_layers'
        st.session_state.setdefault('current_page', 0)
        page_size = st.session_state.get('page_size', self.page_size)
        current_page = st.session_state.get('current_page', 0)
        offset = current_page * page_size

        bio_layers = self.db_manager.list_all_bio_recognition_layers_paginated(page_size, offset)

        st.subheader("🔴 Биораспознающие слои")
        if bio_layers:
            import pandas as pd
            df = pd.DataFrame(bio_layers)
            cols = [c for c in ["BRE_ID", "BRE_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "SN"] if c in df.columns]
            st.dataframe(df[cols], width="stretch")
        else:
            st.info("Нет записей биораспознающих слоев для отображения.")

        st.divider()
        col_prev, col_page, col_next = st.columns([1, 1, 1])
        with col_prev:
            if st.button("◀ Предыдущая", key="bio_prev", disabled=(current_page == 0)):
                st.session_state['current_page'] = max(0, current_page - 1)
                st.rerun()
        with col_page:
            st.markdown(f"**Страница {current_page + 1}**")
        with col_next:
            if st.button("Следующая ▶", key="bio_next", disabled=(len(bio_layers) < page_size)):
                st.session_state['current_page'] = current_page + 1
                st.rerun()

    # streamlit
    def show_immobilization_layers(self):
        """Streamlit-версия: отображение иммобилизационных слоев с пагинацией."""
        st.session_state['current_data_type'] = 'immobilization_layers'
        st.session_state.setdefault('current_page', 0)
        page_size = st.session_state.get('page_size', self.page_size)
        current_page = st.session_state.get('current_page', 0)
        offset = current_page * page_size

        im_layers = self.db_manager.list_all_immobilization_layers_paginated(page_size, offset)

        st.subheader("🟡 Иммобилизационные слои")
        if im_layers:
            import pandas as pd
            df = pd.DataFrame(im_layers)
            cols = [c for c in ["IM_ID", "IM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "MP"] if c in df.columns]
            st.dataframe(df[cols], width="stretch")
        else:
            st.info("Нет записей иммобилизационных слоев для отображения.")

        st.divider()
        col_prev, col_page, col_next = st.columns([1, 1, 1])
        with col_prev:
            if st.button("◀ Предыдущая", key="immob_prev", disabled=(current_page == 0)):
                st.session_state['current_page'] = max(0, current_page - 1)
                st.rerun()
        with col_page:
            st.markdown(f"**Страница {current_page + 1}**")
        with col_next:
            if st.button("Следующая ▶", key="immob_next", disabled=(len(im_layers) < page_size)):
                st.session_state['current_page'] = current_page + 1
                st.rerun()

    # streamlit
    def show_memristive_layers(self):
        """Streamlit-версия: отображение мемристивных слоев с пагинацией."""
        st.session_state['current_data_type'] = 'memristive_layers'
        st.session_state.setdefault('current_page', 0)
        page_size = st.session_state.get('page_size', self.page_size)
        current_page = st.session_state.get('current_page', 0)
        offset = current_page * page_size

        mem_layers = self.db_manager.list_all_memristive_layers_paginated(page_size, offset)

        st.subheader("🟣 Мемристивные слои")
        if mem_layers:
            import pandas as pd
            df = pd.DataFrame(mem_layers)
            cols = [c for c in ["MEM_ID", "MEM_Name", "PH_Min", "PH_Max", "T_Min", "T_Max", "SN"] if c in df.columns]
            st.dataframe(df[cols], width="stretch")
        else:
            st.info("Нет записей мемристивных слоёв для отображения.")

        st.divider()
        col_prev, col_page, col_next = st.columns([1, 1, 1])
        with col_prev:
            if st.button("◀ Предыдущая", key="mem_prev", disabled=(current_page == 0)):
                st.session_state['current_page'] = max(0, current_page - 1)
                st.rerun()
        with col_page:
            st.markdown(f"**Страница {current_page + 1}**")
        with col_next:
            if st.button("Следующая ▶", key="mem_next", disabled=(len(mem_layers) < page_size)):
                st.session_state['current_page'] = current_page + 1
                st.rerun()

    # streamlit version
    def refresh_data(self):
        """Обновление данных в зависимости от текущего типа (Streamlit)."""
        current = st.session_state.get('current_data_type', getattr(self, 'current_data_type', 'analytes'))
        # гарантируем наличие номера страницы
        st.session_state.setdefault('current_page', 0)

        if current == 'analytes':
            self.show_analytes()
        elif current == 'bio_layers':
            self.show_bio_layers()
        elif current == 'immobilization_layers':
            self.show_immobilization_layers()
        elif current == 'memristive_layers':
            self.show_memristive_layers()
        else:
            st.info("Тип данных не выбран или неизвестен")

    # streamlit version
    def update_pagination_buttons(self):
        """Streamlit: отрисовать кнопки пагинации и номер страницы."""
        page = st.session_state.get('current_page', 0)
        page_size = st.session_state.get('page_size', self.page_size)
        data_type = st.session_state.get('current_data_type', 'analytes')

        # Определяем функцию получения данных для текущего типа
        table_map = {
            'analytes': self.db_manager.list_all_analytes_paginated,
            'bio_layers': self.db_manager.list_all_bio_recognition_layers_paginated,
            'immobilization_layers': self.db_manager.list_all_immobilization_layers_paginated,
            'memristive_layers': self.db_manager.list_all_memristive_layers_paginated,
            'sensor_combinations': self.db_manager.list_all_sensor_combinations_paginated
        }
        fetch_fn = table_map.get(data_type)
        # Проверяем наличие следующей страницы (запрашиваем текущую страницу данных)
        if fetch_fn:
            rows = fetch_fn(page_size, page * page_size)
        else:
            rows = []

        disabled_prev = (page == 0)
        disabled_next = (len(rows) < page_size)

        col_prev, col_label, col_next = st.columns([1, 1, 1])
        with col_prev:
            if st.button("◀ Предыдущая", key=f"prev_{data_type}", disabled=disabled_prev, width="stretch"):
                st.session_state['current_page'] = max(0, page - 1)
                st.rerun()
        with col_label:
            st.markdown(f"**Страница {page + 1}**")
        with col_next:
            if st.button("Следующая ▶", key=f"next_{data_type}", disabled=disabled_next, width="stretch"):
                st.session_state['current_page'] = page + 1
                st.rerun()
    
    # streamlit version
    def prev_page(self):
        """Streamlit: переход на предыдущую страницу."""
        page = st.session_state.get('current_page', 0)
        if page > 0:
            st.session_state['current_page'] = page - 1
            st.rerun()

    # streamlit version
    def next_page(self):
        """Streamlit: переход на следующую страницу."""
        page = st.session_state.get('current_page', 0)
        st.session_state['current_page'] = page + 1
        st.rerun()
        
    def computing_combinations(self):
        """рассчет и сохранение комбинаций сенсоров"""
        analytes = self.db_manager.list_all_analytes()
        bio_layers = self.db_manager.list_all_bio_recognition_layers()
        im_layers = self.db_manager.list_all_immobilization_layers()
        mem_layers = self.db_manager.list_all_memristive_layers()

    # streamlit version
    def show_best_combinations(self):
        """Отображение лучших комбинаций сенсоров."""
        st.session_state.analysis_result = "=== ЛУЧШИЕ КОМБИНАЦИИ БИОСЕНСОРОВ ===\n\n"
        
        # Получение всех комбинаций
        sensor_combinations = self.db_manager.list_all_sensor_combinations()
        
        if sensor_combinations:
            for combo in sensor_combinations:
                combo_info = f"""
Комбинация: {combo.get('Combo_ID', 'N/A')}
├─ Аналит: {combo.get('TA_ID', 'N/A')}
├─ Биослой: {combo.get('BRE_ID', 'N/A')}
├─ Иммобилизация: {combo.get('IM_ID', 'N/A')}
├─ Мемристивный слой: {combo.get('MEM_ID', 'N/A')}
└─ Оценка: {combo.get('Score', 'N/A')}"""
                st.session_state.analysis_result += combo_info + "\n"
            st.success("✅ Анализ завершен!")
        else:
            st.session_state.analysis_result += "Нет комбинаций в базе данных."
            st.info("ℹ️ Сначала создайте комбинации сенсоров.")

    # streamlit version
    def comparative_analysis(self):
        """Выполнение сравнительного анализа."""
        st.session_state.analysis_result = "=== СРАВНИТЕЛЬНЫЙ АНАЛИЗ ===\n\n"
        
        try:
            # Подсчет записей в каждой таблице
            analytes = self.db_manager.list_all_analytes()
            bio_layers = self.db_manager.list_all_bio_recognition_layers()
            im_layers = self.db_manager.list_all_immobilization_layers()
            mem_layers = self.db_manager.list_all_memristive_layers()
            
            analysis_text = f"""
                Сравнение составных частей биосенсоров:

                📋 АНАЛИТЫ: {len(analytes)} записей
                {'-' * 40}
                """
            for analyte in analytes[:3]:  # Показываем первые 3
                analysis_text += f"  • {analyte.get('TA_Name', 'N/A')} (pH: {analyte.get('PH_Min')}-{analyte.get('PH_Max')})\n"
            
            analysis_text += f"\n🔴 БИОРАСПОЗНАЮЩИЕ СЛОИ: {len(bio_layers)} записей\n"
            analysis_text += f"{'-' * 40}\n"
            for bio in bio_layers[:3]:  # Показываем первые 3
                analysis_text += f"  • {bio.get('BRE_Name', 'N/A')} (Чувствительность: {bio.get('SN')})\n"
            
            analysis_text += f"\n🟡 ИММОБИЛИЗАЦИОННЫЕ СЛОИ: {len(im_layers)} записей\n"
            analysis_text += f"{'-' * 40}\n"
            for im in im_layers[:3]:  # Показываем первые 3
                analysis_text += f"  • {im.get('IM_Name', 'N/A')} (Модуль: {im.get('MP')})\n"
            
            analysis_text += f"\n🟣 МЕМРИСТИВНЫЕ СЛОИ: {len(mem_layers)} записей\n"
            analysis_text += f"{'-' * 40}\n"
            for mem in mem_layers[:3]:  # Показываем первые 3
                analysis_text += f"  • {mem.get('MEM_Name', 'N/A')} (Чувствительность: {mem.get('SN')})\n"
            
            st.session_state.analysis_result = analysis_text
            st.success("✅ Сравнительный анализ завершен!")
        
        except Exception as e:
            st.session_state.analysis_result = f"Ошибка при выполнении анализа: {str(e)}"
            st.error("❌ Ошибка при выполнении анализа")

    # streamlit version
    @staticmethod
    def show_statistics():
        """Отображение статистики базы данных."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM Analytes")
                analytes_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM BioRecognitionLayers")
                bio_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM ImmobilizationLayers")
                immob_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM MemristiveLayers")
                mem_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM SensorCombinations")
                combo_count = cursor.fetchone()[0]
            
            stats = f"""=== СТАТИСТИКА БАЗЫ ДАННЫХ ===

Количество записей по типам:

📋 Аналиты: {analytes_count}
🔴 Биораспознающие слои: {bio_count}
🟡 Иммобилизационные слои: {immob_count}
🟣 Мемристивные слои: {mem_count}
⚙️  Комбинации сенсоров: {combo_count}

ВСЕГО ЭЛЕМЕНТОВ: {analytes_count + bio_count + immob_count + mem_count + combo_count}"""
            st.session_state.analysis_result = stats
            st.success("✅ Статистика обновлена!")
            
        except Exception as e:
            st.session_state.analysis_result = f"Ошибка получения статистики: {str(e)}"
            st.error("❌ Ошибка при получении статистики")
    
    # streamlit version
    def export_data(self):
        """Экспорт данных в файл (Streamlit)."""
        st.subheader("📤 Экспорт данных")
        choices = {
            "Аналиты": "analytes",
            "Биослои (BRE)": "bio_recognition",
            "Иммобилизационные слои (IM)": "immobilization",
            "Мемристивные слои (MEM)": "memristive",
            "Комбинации сенсоров": "sensor_combinations",
            "Всё": "all"
        }
        choice_label = st.selectbox("Что экспортировать", list(choices.keys()))
        choice = choices[choice_label]
        fmt = st.radio("Формат экспорта", ["csv", "json"], horizontal=True)

        if st.button("Экспортировать"):
            try:
                import pandas as pd
                import io
                import zipfile
                from datetime import datetime

                def fetch_table(key):
                    if key == "analytes":
                        return self.db_manager.list_all_analytes()
                    if key == "bio_recognition":
                        return self.db_manager.list_all_bio_recognition_layers()
                    if key == "immobilization":
                        return self.db_manager.list_all_immobilization_layers()
                    if key == "memristive":
                        return self.db_manager.list_all_memristive_layers()
                    if key == "sensor_combinations":
                        return self.db_manager.list_all_sensor_combinations()
                    return {}

                ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

                if choice == "all":
                    tables = {
                        "analytes": fetch_table("analytes"),
                        "bio_recognition": fetch_table("bio_recognition"),
                        "immobilization": fetch_table("immobilization"),
                        "memristive": fetch_table("memristive"),
                        "sensor_combinations": fetch_table("sensor_combinations"),
                    }
                    if fmt == "json":
                        payload = json.dumps(tables, ensure_ascii=False, indent=2).encode("utf-8")
                        filename = f"all_data_{ts}.json"
                        st.download_button("Скачать JSON", data=payload, file_name=filename, mime="application/json")
                    else:
                        buf = io.BytesIO()
                        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                            for name, rows in tables.items():
                                df = pd.DataFrame(rows)
                                zf.writestr(f"{name}.csv", df.to_csv(index=False).encode("utf-8-sig"))
                        buf.seek(0)
                        st.download_button("Скачать ZIP с CSV", data=buf, file_name=f"all_data_{ts}.zip", mime="application/zip")
                else:
                    rows = fetch_table(choice)
                    if fmt == "json":
                        payload = json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
                        filename = f"{choice}_{ts}.json"
                        st.download_button("Скачать JSON", data=payload, file_name=filename, mime="application/json")
                    else:
                        df = pd.DataFrame(rows)
                        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
                        filename = f"{choice}_{ts}.csv"
                        st.download_button("Скачать CSV", data=csv_bytes, file_name=filename, mime="text/csv")

                st.success("✅ Экспорт выполнен")
            except Exception as e:
                self.logger.exception("Ошибка экспорта данных")
                st.error(f"Ошибка экспорта: {e}")

    # streamlit version
    def about(self):
        """Отображение информации о программе (Streamlit)."""
        info = "Паспорта мемристивных биосенсоров v2.0\n\n© 2025"
        st.info(info)
        try:
            self.logger.info("Показана информация 'О программе'")
        except Exception:
            pass

    def run(self):
        """Главная функция запуска приложения (Streamlit)."""
        # ✅ Регистрируем закрытие БД при завершении
        # atexit.register(self.db_manager.close)
        debug("Приложение запущено")
        if 'analyte_ta_id' in st.session_state:
            ta_id = st.session_state['analyte_ta_id']
            print("Значение переменной:", ta_id)

        # ✅ Инициализируем session_state с помощью setdefault()
        # st.session_state.setdefault('active_section', 'data_entry')
        if 'active_section' not in st.session_state:
            st.session_state['active_section'] = 'data_entry'

        # ✅ Создаём меню в боковой панели
        self.create_menu()
        
        st.divider()
        
        # ✅ Контролируем, что показывать на основе session_state
        active = st.session_state.active_section
        
        if active == 'data_entry':
            st.header("🔬 Ввод паспортов")
            self.create_data_entry_tab()
        
        elif active == 'database':
            st.header("📊 База данных")
            self.create_database_tab()
        
        elif active == 'analysis':
            st.header("📈 Анализ")
            self.create_analysis_tab()
        
        elif active == 'about':
            st.header("ℹ️ О программе")
            self.about()
        
        else:
            # По умолчанию показываем ввод паспортов
            st.header("🔬 Ввод паспортов")
            self.create_data_entry_tab()

        if 'analyte_ta_id' in st.session_state:
            ta_id = st.session_state['analyte_ta_id']
            print("Значение переменной:", ta_id)
            
        # ✅ Создаём вкладки НАПРЯМУЮ (без рекурсии)
        '''tabs = st.tabs([
            "🔬 Ввод паспортов",
            "📊 База данных",
            "📈 Анализ"
        ])
        
        # ✅ Заполняем содержимое вкладок
        with tabs[0]:
            self.create_data_entry_tab()
        
        with tabs[1]:
            self.create_database_tab()
        
        with tabs[2]:
            self.create_analysis_tab()'''