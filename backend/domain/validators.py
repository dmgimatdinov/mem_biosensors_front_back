# domain/validators.py

from typing import Dict, Any, Tuple, Optional
from domain.models import Analyte, BioRecognitionLayer
from domain.config import FIELD_CONSTRAINTS

class DataValidator:
    """Валидация данных моделей."""
    
    @staticmethod
    def validate_analyte(analyte: Analyte) -> Tuple[bool, Optional[str]]:
        """Валидация аналита."""
        # Обязательные поля
        if not analyte.ta_id or not analyte.ta_name:
            return False, "ID и название аналита обязательны"
        
        # Проверка диапазонов
        constraints = FIELD_CONSTRAINTS.get('analyte', {})
        
        if analyte.ph_min is not None:
            c = constraints.get('ph_min', {})
            if not (c.get('min', 0) <= analyte.ph_min <= c.get('max', 14)):
                return False, f"pH_min вне диапазона {c.get('min')}-{c.get('max')}"
        
        if analyte.ph_max is not None:
            c = constraints.get('ph_max', {})
            if not (c.get('min', 0) <= analyte.ph_max <= c.get('max', 14)):
                return False, f"pH_max вне диапазона {c.get('min')}-{c.get('max')}"
        
        # Логическая проверка: ph_min <= ph_max
        if analyte.ph_min and analyte.ph_max and analyte.ph_min > analyte.ph_max:
            return False, "pH_min не может быть больше pH_max"
        
        # Аналогично для других полей...
        
        return True, None
    
    @staticmethod
    def validate_bio_recognition_layer(bio: BioRecognitionLayer) -> Tuple[bool, Optional[str]]:
        """Валидация биослоя."""
        if not bio.bre_id or not bio.bre_name:
            return False, "ID и название биослоя обязательны"
        
        # Логическая проверка диапазонов
        if bio.dr_min and bio.dr_max and bio.dr_min > bio.dr_max:
            return False, "DR_min не может быть больше DR_max"
        
        if bio.t_min and bio.t_max and bio.t_min > bio.t_max:
            return False, "T_min не может быть больше T_max"
        
        return True, None
    
    # Аналогично для immobilization_layer и memristive_layer...
    
class CombinationValidator:
    """Валидация совместимости слоёв сенсора."""
    
    @staticmethod
    def check_ph_compatibility(
        analyte_ph_min: float,
        analyte_ph_max: float,
        *layer_ph_ranges: tuple[float, float],
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверка пересечения диапазонов pH.
        
        Args:
            analyte_ph_min, analyte_ph_max: диапазон pH аналита
            *layer_ph_ranges: кортежи (ph_min, ph_max) для каждого слоя
        """
        for layer_ph_min, layer_ph_max in layer_ph_ranges:
            if not (analyte_ph_min <= layer_ph_max and analyte_ph_max >= layer_ph_min):
                return False, "Диапазоны pH не пересекаются"
        return True, None
    
    @staticmethod
    def check_temperature_compatibility(
        analyte_t_max: float,
        bio_t_min: float,
        bio_t_max: float,
        immob_t_min: float,
        immob_t_max: float,
        mem_t_min: float,
        mem_t_max: float,
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверка температурной совместимости всех слоёв.
        
        Условия:
        1. Все слои работают в пределах T_max аналита
        2. Все слои совместимы по минимальной температуре мемристора
        """
        # Условие 1: макс. температуры слоёв ≤ макс. температура аналита
        if not (bio_t_max <= analyte_t_max and immob_t_max <= analyte_t_max):
            return False, "Температура слоёв превышает T_max аналита"
        
        # Условие 2: мемристор должен быть сверху по T_min
        if not (mem_t_min <= bio_t_min and mem_t_min <= immob_t_min):
            return False, "Рабочая температура мемристора несовместима"
        
        # Условие 3: мемристор должен вмещать диапазоны других слоёв
        if not (bio_t_max <= mem_t_max and immob_t_max <= mem_t_max):
            return False, "Диапазон температур мемристора недостаточен"
        
        return True, None
    
    @staticmethod
    def check_mechanical_compatibility(
        immob_mp: float,
        mem_mp: float,
        mp_tolerance: float = 0.5,
    ) -> Tuple[bool, Optional[str]]:
        """Проверка механической совместимости слоёв."""
        if abs(immob_mp - mem_mp) > mp_tolerance:
            return False, f"Модули Юнга несовместимы (разница > {mp_tolerance})"
        return True, None
    
    @staticmethod
    def validate_combination(
        analyte: Dict[str, Any],
        bio_layer: Dict[str, Any],
        immob_layer: Dict[str, Any],
        mem_layer: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """
        Комплексная проверка совместимости комбинации.
        
        Returns:
            (is_valid, error_message)
        """
        # pH
        ok, msg = CombinationValidator.check_ph_compatibility(
            analyte['PH_Min'], analyte['PH_Max'],
            (bio_layer['PH_Min'], bio_layer['PH_Max']),
            (immob_layer['PH_Min'], immob_layer['PH_Max']),
            (mem_layer['PH_Min'], mem_layer['PH_Max']),
        )
        if not ok:
            return False, msg
        
        # Температура
        ok, msg = CombinationValidator.check_temperature_compatibility(
            analyte['T_Max'],
            bio_layer['T_Min'], bio_layer['T_Max'],
            immob_layer['T_Min'], immob_layer['T_Max'],
            mem_layer['T_Min'], mem_layer['T_Max'],
        )
        if not ok:
            return False, msg
        
        return True, None
