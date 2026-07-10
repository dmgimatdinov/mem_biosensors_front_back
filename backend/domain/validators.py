# domain/validators.py

from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, Optional, List
from domain.models import Analyte, BioRecognitionLayer
from domain.config import FIELD_CONSTRAINTS


@dataclass
class ValidationResult:
    """Результат валидации данных."""
    success: bool
    errors: List[str] = field(default_factory=list)


# Ограничения для строковых полей (префиксы, длина)
STRING_CONSTRAINTS = {
    "analyte": {
        "ta_id": {"prefix": "ta", "min_length": 3, "max_length": 20},
        "ta_name": {"min_length": 3, "max_length": 200},
    },
    "bio_recognition": {
        "bre_id": {"prefix": "bre", "min_length": 4, "max_length": 20},
        "bre_name": {"min_length": 3, "max_length": 200},
    },
    "immobilization": {
        "im_id": {"prefix": "im", "min_length": 3, "max_length": 20},
        "im_name": {"min_length": 3, "max_length": 200},
    },
    "memristive": {
        "mem_id": {"prefix": "mem", "min_length": 4, "max_length": 20},
        "mem_name": {"min_length": 3, "max_length": 200},
    },
}

# Обязательные поля
REQUIRED_FIELDS = {
    "analyte": ["ta_id", "ta_name"],
    "bio_recognition": ["bre_id", "bre_name"],
    "immobilization": ["im_id", "im_name"],
    "memristive": ["mem_id", "mem_name"],
}

# Enum-поля (допустимые значения)
ENUM_FIELDS = {
    "immobilization": {
        "adhesion": ["низкая", "средняя", "высокая", "хорошая", "отличная", "слабая"],
        "solubility": ["водорастворимый", "органический", "нерастворимый"],
    },
}

# Логические связи: min <= max
LOGICAL_PAIRS = {
    "analyte": [("ph_min", "ph_max")],
    "bio_recognition": [("ph_min", "ph_max"), ("t_min", "t_max"), ("dr_min", "dr_max")],
    "immobilization": [],
    "memristive": [("dr_min", "dr_max")],
}

# Маппинг имён полей для отображения в сообщениях об ошибках
FIELD_DISPLAY_NAMES = {
    "ph_min": "pH_min",
    "ph_max": "pH_max",
    "t_min": "T_min",
    "t_max": "T_max",
    "dr_min": "DR_min",
    "dr_max": "DR_max",
}


class DataValidator:
    """Универсальный валидатор данных биосенсора."""

    @staticmethod
    def validate(layer_type: str, data: Dict[str, Any]) -> ValidationResult:
        """
        Универсальный метод валидации для любого слоя.
        
        :param layer_type: analyte | bio_recognition | immobilization | memristive
        :param data: словарь с данными (от фабрик)
        :return: ValidationResult с флагом success и списком ошибок
        """
        errors: List[str] = []

        # 1. СНАЧАЛА проверяем обязательные поля
        missing_fields = []
        for field_name in REQUIRED_FIELDS.get(layer_type, []):
            if field_name not in data or data[field_name] is None or data[field_name] == "":
                missing_fields.append(field_name)

        if missing_fields:
            # Сообщение должно содержать "обязательны"
            errors.append(f"Поля {', '.join(missing_fields)} обязательны")
            return ValidationResult(success=False, errors=errors)

        # 2. Строковые поля (префикс, длина) - регистронезависимая проверка префикса
        for field_name, constraints in STRING_CONSTRAINTS.get(layer_type, {}).items():
            if field_name not in data or data[field_name] is None:
                continue
            value = data[field_name]
            if not isinstance(value, str):
                errors.append(f"Поле '{field_name}' должно быть строкой")
                continue

            # Регистронезависимая проверка префикса
            if "prefix" in constraints and not value.lower().startswith(constraints["prefix"].lower()):
                # Сообщение должно содержать "должен начинаться с"
                errors.append(f"ID должен начинаться с {constraints['prefix']}")
            
            if "min_length" in constraints and len(value) < constraints["min_length"]:
                # Сообщение должно содержать "слишком короткое"
                errors.append(f"Название слишком короткое")
            
            if "max_length" in constraints and len(value) > constraints["max_length"]:
                # Сообщение должно содержать "слишком длинное"
                errors.append(f"Поле '{field_name}' слишком длинное (превышает длину {constraints['max_length']})")

        # 3. Enum-поля
        for field_name, allowed in ENUM_FIELDS.get(layer_type, {}).items():
            if field_name not in data or data[field_name] is None:
                continue
            if data[field_name] not in allowed:
                errors.append(f"Поле '{field_name}' недопустимое значение")

        # 4. Числовые поля по FIELD_CONSTRAINTS
        for field_name, constraints in FIELD_CONSTRAINTS.get(layer_type, {}).items():
            if field_name not in data or data[field_name] is None:
                continue
            value = data[field_name]
            if not isinstance(value, (int, float)):
                errors.append(f"Поле '{field_name}' должно быть числом")
                continue

            min_val = constraints.get("min")
            max_val = constraints.get("max")
            
            # Используем отображаемое имя поля (с заглавными буквами)
            display_name = FIELD_DISPLAY_NAMES.get(field_name, field_name)
            
            if min_val is not None and value < min_val:
                errors.append(f"Поле '{display_name}' вне диапазона")
            if max_val is not None and value > max_val:
                errors.append(f"Поле '{display_name}' вне диапазона")

        # 5. Логические связи (min <= max)
        for min_f, max_f in LOGICAL_PAIRS.get(layer_type, []):
            if min_f in data and max_f in data:
                v_min, v_max = data[min_f], data[max_f]
                if v_min is not None and v_max is not None and v_min > v_max:
                    # Используем отображаемые имена
                    display_min = FIELD_DISPLAY_NAMES.get(min_f, min_f)
                    display_max = FIELD_DISPLAY_NAMES.get(max_f, max_f)
                    errors.append(f"{display_min} не может быть больше {display_max}")

        return ValidationResult(success=len(errors) == 0, errors=errors)

    # --- Старые методы (сохранены для обратной совместимости) ---

    @staticmethod
    def validate_analyte(analyte: Analyte) -> Tuple[bool, Optional[str]]:
        """Валидация аналита (обратная совместимость)."""
        result = DataValidator.validate("analyte", analyte.__dict__)
        if result.success:
            return True, None
        return False, result.errors[0] if result.errors else "Ошибка валидации"

    @staticmethod
    def validate_bio_recognition_layer(bio: BioRecognitionLayer) -> Tuple[bool, Optional[str]]:
        """Валидация биослоя (обратная совместимость)."""
        result = DataValidator.validate("bio_recognition", bio.__dict__)
        if result.success:
            return True, None
        return False, result.errors[0] if result.errors else "Ошибка валидации"
    
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
        mp_tolerance: float = 50.0,
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

        # Механика
        immob_mp = immob_layer.get('MP', immob_layer.get('young_modulus', 0))
        mem_mp = mem_layer.get('MP', mem_layer.get('young_modulus', 0))
        ok, msg = CombinationValidator.check_mechanical_compatibility(immob_mp, mem_mp)
        if not ok:
            return False, msg
        
        return True, None
