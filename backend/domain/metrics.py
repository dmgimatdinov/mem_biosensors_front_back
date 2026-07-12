# domain/metrics.py

import math
from typing import Any, Dict, List, Optional, Tuple

from services.score_normalizer import calculate_score

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


_METRIC_KEYS = {
    'sn_total': ('sn_total', 'SN_total', 'SN'),
    'tr_total': ('tr_total', 'TR_total', 'TR'),
    'st_total': ('st_total', 'ST_total', 'ST'),
    'lod_total': ('lod_total', 'LOD_total', 'LOD'),
    'dr_total': ('dr_total', 'DR_total', 'DR'),
    'pc_total': ('pc_total', 'PC_total', 'PC'),
}

_TYPICAL_RANGES = {
    'sn_total': (100.0, 20000.0),
    'tr_total': (1.0, 3600.0),
    'st_total': (1.0, 365.0),
    'lod_total': (1.0, 50000.0),
    'dr_total': (1.0, 1000.0),
    'pc_total': (1.0, 2000.0),
}

_LOWER_IS_BETTER = {'tr_total', 'lod_total', 'pc_total'}

_CATEGORY_ALPHA = {
    'high': 0.2,
    'medium': 0.5,
    'low': 0.8,
}


def _pick_metric(structure: Dict[str, Any], canonical_key: str) -> Optional[float]:
    for key in _METRIC_KEYS[canonical_key]:
        if key in structure and structure[key] is not None:
            return float(structure[key])
    return None


def _build_metrics(structure: Dict[str, Any], fill_mode: str) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    for key, bounds in _TYPICAL_RANGES.items():
        value = _pick_metric(structure, key)
        if value is not None:
            metrics[key] = value
            continue

        low, high = bounds
        if fill_mode == 'worst':
            metrics[key] = high if key in _LOWER_IS_BETTER else low
        elif fill_mode == 'best':
            metrics[key] = low if key in _LOWER_IS_BETTER else high
        else:
            metrics[key] = (low + high) / 2.0
    return metrics


def _extract_layer_reliability(structure: Dict[str, Any]) -> Tuple[List[float], List[str]]:
    completeness: List[float] = []
    categories: List[str] = []
    for key in ('analyte', 'bio_layer', 'bio', 'immobilization_layer', 'immob', 'memristive_layer', 'mem'):
        layer = structure.get(key)
        if not isinstance(layer, dict):
            continue

        comp = layer.get('data_completeness')
        if comp is not None:
            try:
                completeness.append(max(0.0, min(1.0, float(comp))))
            except (TypeError, ValueError):
                pass

        category = layer.get('reliability_category')
        if isinstance(category, str):
            category = category.lower().strip()
            if category in _CATEGORY_ALPHA:
                categories.append(category)
    return completeness, categories


def calculate_reliability_coefficient(eta: float, alpha: float, gamma: float) -> float:
    """Вычисляет коэффициент достоверности κ = (1 - α * (1 - η))^γ."""
    eta = max(0.0, min(1.0, float(eta)))
    alpha = max(0.0, min(1.0, float(alpha)))
    gamma = max(0.0, float(gamma))
    base = max(0.0, 1.0 - alpha * (1.0 - eta))
    return float(base ** gamma)


def calculate_final_score(raw_score: float, kappa: float) -> float:
    """Применяет коэффициент достоверности к итоговому баллу."""
    return float(raw_score) * max(0.0, min(1.0, float(kappa)))


def calculate_interval_score(structure: Dict[str, Any], strategy: str) -> Tuple[float, float, float]:
    """
    Возвращает интервальную оценку (min, max, delta) при неполных данных.

    strategy:
    - pessimistic: узкий интервал в нижней части
    - optimistic: узкий интервал в верхней части
    - average: полный интервал
    """
    if strategy not in {'pessimistic', 'optimistic', 'average'}:
        raise ValueError("strategy must be one of: pessimistic, optimistic, average")

    score_worst = calculate_score(_build_metrics(structure, fill_mode='worst'))
    score_best = calculate_score(_build_metrics(structure, fill_mode='best'))
    score_mid = calculate_score(_build_metrics(structure, fill_mode='mid'))

    low = min(score_worst, score_best)
    high = max(score_worst, score_best)

    if strategy == 'pessimistic':
        score_min, score_max = low, min(high, score_mid)
    elif strategy == 'optimistic':
        score_min, score_max = max(low, score_mid), high
    else:
        score_min, score_max = low, high

    return score_min, score_max, (score_max - score_min)


def infer_reliability_inputs(structure: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Выводит (eta, alpha, gamma) из структуры.

    Для старых данных без reliability_category и data_completeness возвращает
    eta=1.0, alpha=0.0, gamma=1.0, что даёт κ=1.0.
    """
    completeness, categories = _extract_layer_reliability(structure)

    if completeness:
        eta = sum(completeness) / len(completeness)
    else:
        present = 0
        total = len(_TYPICAL_RANGES)
        for key in _TYPICAL_RANGES:
            if _pick_metric(structure, key) is not None:
                present += 1
        eta = present / total if total else 1.0

    if categories:
        alpha = sum(_CATEGORY_ALPHA[c] for c in categories) / len(categories)
    else:
        alpha = 0.0

    gamma = float(structure.get('reliability_gamma', 1.0 if not categories else 2.0))
    return eta, alpha, gamma


def suggest_critical_gaps(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Возвращает приоритизированный список критичных пропусков, если κ < 0.6."""
    eta, alpha, gamma = infer_reliability_inputs(structure)
    kappa = calculate_reliability_coefficient(eta, alpha, gamma)
    if kappa >= 0.6:
        return []

    base_metrics = _build_metrics(structure, fill_mode='mid')
    base_score = calculate_score(base_metrics)
    gaps: List[Dict[str, Any]] = []

    for key in _TYPICAL_RANGES:
        if _pick_metric(structure, key) is not None:
            continue

        low, high = _TYPICAL_RANGES[key]
        candidate = dict(base_metrics)
        # Приближение чувствительности dScore/dx_j по конечной разности.
        candidate[key] = low if key in _LOWER_IS_BETTER else high
        improved_score = calculate_score(candidate)
        impact = abs(improved_score - base_score)

        if impact >= 1.0:
            priority = 'high'
        elif impact >= 0.5:
            priority = 'medium'
        else:
            priority = 'low'

        effort = 'medium'
        if key in {'tr_total', 'pc_total'}:
            effort = 'low'
        elif key in {'sn_total', 'dr_total'}:
            effort = 'high'

        gaps.append({
            'parameter': key,
            'priority': priority,
            'impact': round(impact, 4),
            'method': 'finite_difference_sensitivity',
            'effort': effort,
        })

    gaps.sort(key=lambda item: item['impact'], reverse=True)
    return gaps
