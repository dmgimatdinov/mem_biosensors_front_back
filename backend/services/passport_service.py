# services/passport_service.py

from db.manager import DatabaseManager
from domain.models import (
    Analyte, BioRecognitionLayer, ImmobilizationLayer, 
    MemristiveLayer, SensorCombination, Passport
)
from typing import Tuple, Optional

class PassportService:
    """Бизнес-логика для сохранения/загрузки паспортов."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def save_passport(
        self,
        analyte: Analyte,
        bio_layer: BioRecognitionLayer,
        immobilization_layer: ImmobilizationLayer,
        memristive_layer: MemristiveLayer,
        combination: Optional[SensorCombination] = None,
    ) -> Tuple[bool, str]:
        """Сохранение полного паспорта с валидацией."""
        
        try:
            # Валидация ID
            if not analyte.ta_id:
                return False, "❌ ID аналита не может быть пустым"
            if not bio_layer.bre_id:
                return False, "❌ ID биослоя не может быть пустым"
            if not immobilization_layer.im_id:
                return False, "❌ ID иммобилизации не может быть пустым"
            if not memristive_layer.mem_id:
                return False, "❌ ID мемристора не может быть пустым"
            
            # Сохранение каждого слоя
            results = []
            
            # Аналит
            analyte_dict = self._dataclass_to_db_dict(analyte, 'TA')
            res = self.db.insert_analyte(analyte_dict)
            results.append(('Аналит', res, analyte.ta_id))
            
            # Биослой
            bio_dict = self._dataclass_to_db_dict(bio_layer, 'BRE')
            res = self.db.insert_bio_recognition_layer(bio_dict)
            results.append(('Биослой', res, bio_layer.bre_id))
            
            # Иммобилизация
            immob_dict = self._dataclass_to_db_dict(immobilization_layer, 'IM')
            res = self.db.insert_immobilization_layer(immob_dict)
            results.append(('Иммобилизация', res, immobilization_layer.im_id))
            
            # Мемристор
            mem_dict = self._dataclass_to_db_dict(memristive_layer, 'MEM')
            res = self.db.insert_memristive_layer(mem_dict)
            results.append(('Мемристор', res, memristive_layer.mem_id))
            
            # Комбинация (если передана)
            if combination:
                combo_dict = self._dataclass_to_db_dict(combination, 'Combo')
                res = self.db.insert_sensor_combination(combo_dict)
                results.append(('Комбинация', res, combination.combo_id))
            
            # Проверка результатов
            duplicates = []
            errors = []
            
            for entity_name, result, entity_id in results:
                if result == "DUPLICATE":
                    duplicates.append((entity_name, entity_id))
                elif result is not True:
                    errors.append((entity_name, entity_id))
            
            # Обработка дубликатов и ошибок
            if duplicates:
                return False, ("DUPLICATE", duplicates)  # специальный код для UI
            if errors:
                return False, f"❌ Ошибка сохранения: {', '.join([f'{e[0]} {e[1]}' for e in errors])}"
            
            return True, "✅ Все данные успешно сохранены!"
        
        except Exception as e:
            return False, f"❌ Критическая ошибка: {str(e)}"
    
    def overwrite_entity(self, entity_type: str, entity_id: str) -> bool:
        """Перезаписать существующую сущность."""
        from db.manager import get_connection
        import sqlite3
        
        table_map = {
            'analyte': 'Analytes',
            'bio': 'BioRecognitionLayers',
            'immob': 'ImmobilizationLayers',
            'mem': 'MemristiveLayers',
            'combo': 'SensorCombinations',
        }
        
        id_map = {
            'analyte': 'TA_ID',
            'bio': 'BRE_ID',
            'immob': 'IM_ID',
            'mem': 'MEM_ID',
            'combo': 'Combo_ID',
        }
        
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM {table_map[entity_type]} WHERE {id_map[entity_type]} = ?",
                    (entity_id,)
                )
                conn.commit()
            return True
        except sqlite3.Error:
            return False
    
    @staticmethod
    def _dataclass_to_db_dict(obj, prefix: str) -> dict:
        """Конвертация dataclass в dict для БД с преобразованием имён."""
        from dataclasses import asdict
        
        db_dict = asdict(obj)
        
        # Маппинг имён полей из Python в SQL (snake_case → UPPERCASE)
        name_map = {
            'ta_id': 'TA_ID', 'ta_name': 'TA_Name',
            'bre_id': 'BRE_ID', 'bre_name': 'BRE_Name',
            'im_id': 'IM_ID', 'im_name': 'IM_Name',
            'mem_id': 'MEM_ID', 'mem_name': 'MEM_Name',
            'combo_id': 'Combo_ID',
            'sn_total': 'SN_total', 'tr_total': 'TR_total',
            'st_total': 'ST_total', 'rp_total': 'RP_total',
            'lod_total': 'LOD_total', 'dr_total': 'DR_total',
            'hl_total': 'HL_total', 'pc_total': 'PC_total',
            'score': 'Score',
            'ph_min': 'PHMin', 'ph_max': 'PHMax', 't_min': 'TMin', 't_max': 'TMax',
            'stability': 'ST', 'half_life': 'HL','durability': 'HL',
            'power_consumption': 'PC',
            'sensitivity': 'SN', 'young_modulus': 'MP',
            'reproducibility': 'RP', 'response_time': 'TR', 'lod': 'LOD',
            'loss_coefficient': 'KIM', 'adhesion': 'Adh', 'solubility': 'Sol',
            'dr_min': 'DRMin', 'dr_max': 'DRMax'
        }
        
        converted = {}
        for key, val in db_dict.items():
            db_key = name_map.get(key, key)
            converted[db_key] = val
        
        return converted
