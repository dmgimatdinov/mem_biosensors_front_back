# domain/metrics.py

import math
from typing import Optional

class MetricsNormalizer:
    """Нормализация метрик сенсора в диапазон 0-1."""
    
    # Эталонные значения для нормализации (можно настраивать)
    REFERENCE_VALUES = {
        'SN': 1000.0,          # Чувствительность
        'TR': 3600.0,          # Время отклика (с)
        'ST': 365.0,           # Стабильность (дни)
        'RP': 100.0,           # Воспроизводимость (%)
        'LOD': 50000.0,        # Предел обнаружения (нМ)
        'DR': 1e10,            # Диапазон
        'HL': 8760.0,          # Долговечность (ч)
        'PC': 1000.0,          # Энергопотребление (мВт)
    }
    
    @staticmethod
    def normalize(value: Optional[float], kind: str = 'default') -> float:
        """
        Нормализация значения в диапазон 0-1.
        
        Args:
            value: значение для нормализации
            kind: тип метрики (SN, TR, ST, RP, LOD, DR, HL, PC)
        
        Returns:
            нормализованное значение 0-1, где 1 = максимально хорошее значение
        """
        if value is None or value == 0:
            return 0.0
        
        # "Меньше лучше" метрики: TR, LOD, PC
        if kind in ['TR', 'LOD', 'PC']:
            # Инверсия: чем меньше, тем выше балл
            ref = MetricsNormalizer.REFERENCE_VALUES.get(kind, 1.0)
            # Используем логарифмическую шкалу для широких диапазонов
            if value <= 0:
                return 0.0
            normalized = ref / value
            return min(1.0, math.log(normalized + 1) / math.log(ref + 1))
        
        # "Больше лучше" метрики: SN, ST, RP, DR, HL
        else:
            ref = MetricsNormalizer.REFERENCE_VALUES.get(kind, 1.0)
            if ref <= 0:
                return 0.0
            # Линейная нормализация с логарифмом для больших значений
            normalized = min(value / ref, 10.0)  # Порог максимума
            return math.log(normalized + 1) / math.log(11.0)  # log-scale
    
    @staticmethod
    def set_reference(kind: str, value: float):
        """Переопределение эталонного значения для метрики."""
        MetricsNormalizer.REFERENCE_VALUES[kind] = value
