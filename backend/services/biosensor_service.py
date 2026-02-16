# services/biosensor_service.py
from domain.config import FIELD_CONSTRAINTS
# from typing import Dict, Any, Optional

from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Унифицированный результат валидации"""
    is_valid: bool
    entity_type: str
    entity_id: Optional[str]
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def __bool__(self) -> bool:
        return self.is_valid

# Универсальная конфигурация SENSOR_LAYERS_CONFIG на основе FIELD_CONSTRAINTS
SENSOR_LAYERS_CONFIG = {
    'analyte': {
        'required_fields': {'ta_id', 'ta_name'},
        'constraints': {
            'ta_id': {'type': str, 'pattern': r'^TA[A-Z0-9_-]{1,20}$'},
            'ta_name': {'type': str, 'min_length': 3, 'max_length': 255},
            'ph_min': {'type': float, 'min': 2.0, 'max': 10.0},
            'ph_max': {'type': float, 'min': 2.0, 'max': 10.0},
            't_max': {'type': int, 'min': 0, 'max': 180},
            'stability': {'type': int, 'min': 0, 'max': 365},
            'half_life': {'type': int, 'min': 0, 'max': 8760},
            'power_consumption': {'type': int, 'min': 0, 'max': 1000},
        },
        'id_field': 'ta_id'
    },
    
    'bio_recognition': {
        'required_fields': {'bre_id', 'bre_name'},
        'constraints': {
            'bre_id': {'type': str, 'pattern': r'^BRE[A-Z0-9_-]{1,20}$'},
            'bre_name': {'type': str, 'min_length': 3, 'max_length': 255},
            'ph_min': {'type': float, 'min': 2.0, 'max': 10.0},
            'ph_max': {'type': float, 'min': 2.0, 'max': 10.0},
            't_min': {'type': int, 'min': 4, 'max': 120},
            't_max': {'type': int, 'min': 4, 'max': 120},
            'sensitivity': {'type': int, 'min': 0, 'max': 20000},
            'reproducibility': {'type': int, 'min': 0, 'max': 100},
            'response_time': {'type': int, 'min': 0, 'max': 3600},
            'stability': {'type': int, 'min': 0, 'max': 365},
            'lod': {'type': int, 'min': 0, 'max': 50000},
            'durability': {'type': int, 'min': 0, 'max': 8760},
            'power_consumption': {'type': int, 'min': 0, 'max': 1000},
            'dr_min': {'type': float, 'min': 0.1, 'max': 1000000000000.0},
            'dr_max': {'type': float, 'min': 0.1, 'max': 1000000000000.0},
        },
        'id_field': 'bre_id'
    },
    
    'immobilization': {
        'required_fields': {'im_id', 'im_name'},
        'constraints': {
            'im_id': {'type': str, 'pattern': r'^IM[A-Z0-9_-]{1,20}$'},
            'im_name': {'type': str, 'min_length': 3, 'max_length': 255},
            'ph_min': {'type': float, 'min': 2.0, 'max': 10.0},
            'ph_max': {'type': float, 'min': 2.0, 'max': 10.0},
            't_min': {'type': int, 'min': 4, 'max': 120},
            't_max': {'type': int, 'min': 4, 'max': 120},
            'young_modulus': {'type': int, 'min': 0, 'max': 1000},
            'loss_coefficient': {'type': float, 'min': 0.0, 'max': 1.0},
            'reproducibility': {'type': int, 'min': 0, 'max': 100},
            'response_time': {'type': int, 'min': 0, 'max': 3600},
            'stability': {'type': int, 'min': 0, 'max': 365},
            'durability': {'type': int, 'min': 0, 'max': 8760},
            'power_consumption': {'type': int, 'min': 0, 'max': 1000},
            # Строчные поля из FORMS_CONFIG
            'adhesion': {'type': str, 'enum': ['слабая', 'хорошая', 'отличная']},
            'solubility': {'type': str, 'enum': ['водорастворимый', 'органический', 'нерастворимый']},
        },
        'id_field': 'im_id'
    },
    
    'memristive': {
        'required_fields': {'mr_id', 'mr_name'},
        'constraints': {
            'mr_id': {'type': str, 'pattern': r'^MR[A-Z0-9_-]{1,20}$'},
            'mr_name': {'type': str, 'min_length': 3, 'max_length': 255},
            'ph_min': {'type': float, 'min': 2.0, 'max': 10.0},
            'ph_max': {'type': float, 'min': 2.0, 'max': 10.0},
            't_min': {'type': int, 'min': 5, 'max': 120},
            't_max': {'type': int, 'min': 5, 'max': 120},
            'dr_min': {'type': float, 'min': 0.0000001, 'max': 100000000000.0},
            'dr_max': {'type': float, 'min': 0.0000001, 'max': 100000000000.0},
            'young_modulus': {'type': int, 'min': 0, 'max': 1000},
            'sensitivity': {'type': int, 'min': 0, 'max': 1000},
            'reproducibility': {'type': int, 'min': 0, 'max': 100},
            'response_time': {'type': int, 'min': 0, 'max': 3600},
            'stability': {'type': int, 'min': 0, 'max': 365},
            'lod': {'type': int, 'min': 0, 'max': 100000},
            'durability': {'type': int, 'min': 0, 'max': 100000},
            'power_consumption': {'type': int, 'min': 0, 'max': 1000},
        },
        'id_field': 'mr_id'
    }
}


class ConstraintValidator:
    """Универсальный валидатор ограничений"""
    
    @staticmethod
    def validate_type(value: Any, expected_type: Type) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, expected_type):
            return f"Ожидается {expected_type.__name__}, получено {type(value).__name__}"
        return None
    
    @staticmethod
    def validate_range(value: float, constraint: Dict[str, float]) -> Optional[str]:
        if 'min' in constraint and value < constraint['min']:
            return f"меньше минимума {constraint['min']}"
        if 'max' in constraint and value > constraint['max']:
            return f"больше максимума {constraint['max']}"
        return None
    
    @staticmethod
    def validate_length(value: str, constraint: Dict[str, int]) -> Optional[str]:
        length = len(value)
        if 'min_length' in constraint and length < constraint['min_length']:
            return f"длина {length} < {constraint['min_length']}"
        if 'max_length' in constraint and length > constraint['max_length']:
            return f"длина {length} > {constraint['max_length']}"
        return None
    
    @staticmethod
    def validate_enum(value: str, constraint: Dict) -> Optional[str]:
        allowed = constraint.get('enum', [])
        if value not in allowed:
            return f"не в списке: {allowed}"
        return None
    
    @staticmethod
    def validate_pattern(value: str, constraint: Dict) -> Optional[str]:
        pattern = constraint.get('pattern')
        if pattern and not re.match(pattern, value):
            return f"не соответствует шаблону"
        return None

class UniversalBiosensorValidator:
    """Универсальный валидатор для всех слоев биосенсора"""
    
    def __init__(self, config: Dict[str, Dict] = None, db=None):
        self.config = config or SENSOR_LAYERS_CONFIG
        self.db = db
        self.constraint_validator = ConstraintValidator()
    
    def validate(self, entity_type: str, data: Dict[str, Any]) -> ValidationResult:
        """Универсальная валидация для любого слоя"""
        if entity_type not in self.config:
            return ValidationResult(False, entity_type, None, [f"Неизвестный тип: {entity_type}"])
        
        layer_config = self.config[entity_type]
        entity_id = data.get(layer_config['id_field'])
        
        result = ValidationResult(True, entity_type, entity_id)
        
        # 1. Обязательные поля
        for required_field in layer_config['required_fields']:
            if not data.get(required_field):
                result.add_error(f"Обязательное поле '{required_field}' отсутствует")
        
        # 2. Ограничения для всех полей
        constraints = layer_config.get('constraints', {})
        for field, value in data.items():
            if value is None or field not in constraints:
                continue
            
            constraint = constraints[field]
            
            # Тип
            if 'type' in constraint:
                type_error = self.constraint_validator.validate_type(value, constraint['type'])
                if type_error:
                    result.add_error(f"{field}: {type_error}")
                    continue
            
            # Диапазон (числа)
            if isinstance(value, (int, float)) and any(k in constraint for k in ['min', 'max']):
                range_error = self.constraint_validator.validate_range(value, constraint)
                if range_error:
                    result.add_error(f"{field}: {range_error}")
            
            # Длина (строки)
            if isinstance(value, str) and any(k in constraint for k in ['min_length', 'max_length']):
                length_error = self.constraint_validator.validate_length(value, constraint)
                if length_error:
                    result.add_error(f"{field}: {length_error}")
            
            # Enum
            if isinstance(value, str) and 'enum' in constraint:
                enum_error = self.constraint_validator.validate_enum(value, constraint)
                if enum_error:
                    result.add_error(f"{field}: {enum_error}")
            
            # Pattern
            if isinstance(value, str) and 'pattern' in constraint:
                pattern_error = self.constraint_validator.validate_pattern(value, constraint)
                if pattern_error:
                    result.add_error(f"{field}: {pattern_error}")
        
        # 3. Уникальность (если БД доступна)
        if self.db and entity_id and result.is_valid:
            if self.db.entity_exists(entity_type, layer_config['id_field'], entity_id):
                result.add_error(f"{entity_type} {entity_id} уже существует")
        
        logger.info(f"Валидация {entity_type}#{entity_id}: "
                   f"{'✓ OK' if result.is_valid else f'✗ {len(result.errors)} ошибок'}")
        return result

class DatabaseAdapter(ABC):
    """Абстрактный адаптер БД"""
    
    @abstractmethod
    def insert(self, entity_type: str, data: Dict[str, Any]) -> Any:
        pass
    
    @abstractmethod
    def list_all_paginated(self, entity_type: str, limit: int, offset: int) -> List[Dict]:
        pass
    
    @abstractmethod
    def entity_exists(self, entity_type: str, field: str, value: Any) -> bool:
        pass

class UniversalCRUDManager:
    """Универсальный менеджер CRUD операций"""
    
    def __init__(self, validator: UniversalBiosensorValidator, db: DatabaseAdapter):
        self.validator = validator
        self.db = db
    
    def create(self, entity_type: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """Создание сущности любого слоя с валидацией"""
        result = self.validator.validate(entity_type, data)
        
        if not result:
            return False, "; ".join(result.errors)
        
        # Сохранение в БД
        db_result = self.db.insert(entity_type, data)
        
        if db_result is True:
            return True, f"{entity_type} {result.entity_id} сохранён"
        elif db_result == "DUPLICATE":
            return False, f"{entity_type} {result.entity_id} уже существует"
        else:
            return False, f"Ошибка при сохранении: {db_result}"
    
    def list(self, entity_type: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Получение списка сущностей с пагинацией"""
        return self.db.list_all_paginated(entity_type, limit, offset)


class BiosensorService:
    def __init__(self, db: DatabaseAdapter):
        self.validator = UniversalBiosensorValidator(SENSOR_LAYERS_CONFIG, db)
        self.crud = UniversalCRUDManager(self.validator, db)
        self.db = db
        
    # Универсальные методы
    def validate_entity(self, entity_type: str, data: Dict[str, Any]) -> ValidationResult:
        """Валидация любого слоя"""
        return self.validator.validate(entity_type, data)
    
    def save_entity(self, entity_type: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """Сохранение любого слоя"""
        return self.crud.create(entity_type, data)
    
    def get_all_entities(self, entity_type: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Получение списка любого слоя"""
        return self.crud.list(entity_type, limit, offset)

# class BiosensorService:
#     """Бизнес-логика для работы с биосенсорами (без Streamlit)."""
    
#     def __init__(self, db: DatabaseManager):
#         self.db = db
    
#     def validate_field(self, entity_type: str, field_name: str, value: float) -> bool:
#         """Валидация поля по ограничениям"""
#         if entity_type not in FIELD_CONSTRAINTS:
#             return True
#         if field_name not in FIELD_CONSTRAINTS[entity_type]:
#             return True
        
#         constraint = FIELD_CONSTRAINTS[entity_type][field_name]
#         return constraint['min'] <= value <= constraint['max']
    
#     def validate_analyte(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
#         """Валидация данных аналита"""
#         if not data.get('ta_id'):
#             return False, "ID аналита обязателен"
#         if not data.get('ta_name'):
#             return False, "Название обязательно"
        
#         # Проверка типов и диапазонов
#         for field, value in data.items():
#             if value is not None and field in FIELD_CONSTRAINTS['analyte']:
#                 if not self.validate_field('analyte', field, value):
#                     constraint = FIELD_CONSTRAINTS['analyte'][field]
#                     return False, f"{field}: значение вне диапазона {constraint['min']}-{constraint['max']}"
        
#         return True, None
    
#     def save_analyte(self, data: Dict[str, Any]) -> tuple[bool, str]:
#         """Сохранение аналита (с валидацией)"""
#         is_valid, error_msg = self.validate_analyte(data)
#         if not is_valid:
#             return False, error_msg
        
#         result = self.db.insert_analyte(data)
#         if result is True:
#             return True, f"Аналит {data['ta_id']} сохранён"
#         elif result == "DUPLICATE":
#             return False, f"Аналит {data['ta_id']} уже существует"
#         else:
#             return False, "Ошибка при сохранении"
    
#     def get_all_analytes(self, limit: int = 50, offset: int = 0) -> list[Dict]:
#         """Получение аналитов с пагинацией"""
#         return self.db.list_all_analytes_paginated(limit, offset)
