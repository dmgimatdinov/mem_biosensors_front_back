# services/combination_synthesis.py

from db.manager import DatabaseManager, TableConfig
from domain.validators import CombinationValidator
from domain.metrics import MetricsNormalizer
from domain.models import SensorCombination
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class CombinationSynthesisService:
    """Синтез и оценка комбинаций сенсоров."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def synthesize_all_combinations(self, max_combinations: int = 10000) -> Tuple[int, int]:
        """
        Синтез всех совместимых комбинаций.
        
        Args:
            max_combinations: максимальное количество для процессинга
        
        Returns:
            (total_checked, successfully_created)
        """
        analytes = self.db.list_all_analytes()
        bio_layers = self.db.list_all_bio_recognition_layers()
        immob_layers = self.db.list_all_immobilization_layers()
        mem_layers = self.db.list_all_memristive_layers()
        
        total_possible = len(analytes) * len(bio_layers) * len(immob_layers) * len(mem_layers)
        
        if total_possible > max_combinations:
            logger.warning(
                f"Возможных комбинаций: {total_possible}, "
                f"лимит: {max_combinations}. Синтез может быть неполным."
            )
        
        total_checked = 0
        successfully_created = 0
        
        for analyte in analytes:
            for bio_layer in bio_layers:
                for immob_layer in immob_layers:
                    for mem_layer in mem_layers:
                        if total_checked >= max_combinations:
                            logger.info(f"Достигнут лимит {max_combinations} комбинаций")
                            return total_checked, successfully_created
                        
                        total_checked += 1
                        
                        try:
                            result = self.create_combination(
                                analyte, bio_layer, immob_layer, mem_layer
                            )
                            if result:
                                successfully_created += 1
                        except Exception as e:
                            logger.error(f"Ошибка при создании комбинации: {e}")
        
        logger.info(f"Синтез завершён: {total_checked} проверено, {successfully_created} создано")
        return total_checked, successfully_created
    
    def create_combination(
        self,
        analyte: Dict[str, Any],
        bio_layer: Dict[str, Any],
        immob_layer: Dict[str, Any],
        mem_layer: Dict[str, Any],
    ) -> bool:
        """
        Создание комбинации с валидацией и расчётом метрик.
        
        Returns:
            True если комбинация создана, False иначе
        """
        # Валидация совместимости
        is_valid, error_msg = CombinationValidator.validate_combination(
            analyte, bio_layer, immob_layer, mem_layer
        )
        if not is_valid:
            logger.debug(f"Комбинация {analyte['TA_ID']}-{bio_layer['BRE_ID']}-{immob_layer['IM_ID']}-{mem_layer['MEM_ID']}: {error_msg}")
            return False
        
        # Расчёт интегральных метрик
        metrics = self._calculate_metrics(analyte, bio_layer, immob_layer, mem_layer)
        
        # Расчёт Score
        score = self._calculate_score(metrics)
        
        # ID комбинации
        combo_id = f"COMBO_{analyte['TA_ID']}_{bio_layer['BRE_ID']}_{immob_layer['IM_ID']}_{mem_layer['MEM_ID']}"
        
        # Подготовка данных для БД
        combination_data = {
            'Combo_ID': combo_id,
            'TA_ID': analyte['TA_ID'],
            'BRE_ID': bio_layer['BRE_ID'],
            'IM_ID': immob_layer['IM_ID'],
            'MEM_ID': mem_layer['MEM_ID'],
            'SN_total': metrics['SN_total'],
            'TR_total': metrics['TR_total'],
            'ST_total': metrics['ST_total'],
            'RP_total': metrics['RP_total'],
            'LOD_total': metrics['LOD_total'],
            'DR_total': metrics['DR_total'],
            'HL_total': metrics['HL_total'],
            'PC_total': metrics['PC_total'],
            'Score': score,
            'created_at': None,
        }
        
        result = self.db.insert_sensor_combination(combination_data)
        
        if result is True:
            logger.info(f"✅ Комбинация {combo_id} создана (Score: {score:.3f})")
            return True
        elif result == "DUPLICATE":
            logger.debug(f"⚠️ Комбинация {combo_id} уже существует")
            return False
        else:
            logger.error(f"❌ Ошибка при добавлении комбинации {combo_id}")
            return False
    
    @staticmethod
    def _calculate_metrics(
        analyte: Dict, bio: Dict, immob: Dict, mem: Dict
    ) -> Dict[str, float]:
        """Расчёт интегральных характеристик комбинации."""
        metrics = {}
        
        # Чувствительность (произведение + K_IM)
        metrics['SN_total'] = bio.get('SN', 0) * mem.get('SN', 0) * immob.get('K_IM', 1)
        
        # Время отклика (сумма)
        metrics['TR_total'] = bio.get('TR', 0) + immob.get('TR', 0) + mem.get('TR', 0)
        
        # Стабильность (минимум)
        metrics['ST_total'] = min(bio.get('ST', 0), immob.get('ST', 0), mem.get('ST', 0))
        
        # Воспроизводимость (минимум)
        metrics['RP_total'] = min(bio.get('RP', 0), immob.get('RP', 0), mem.get('RP', 0))
        
        # Предел обнаружения (максимум = хуже)
        metrics['LOD_total'] = max(bio.get('LOD', 0), mem.get('LOD', 0))
        
        # Диапазон (пересечение)
        bio_dr_min = bio.get('DR_Min', 0)
        bio_dr_max = bio.get('DR_Max', float('inf'))
        mem_dr_min = mem.get('DR_Min', 0)
        mem_dr_max = mem.get('DR_Max', float('inf'))
        
        dr_min = max(bio_dr_min, mem_dr_min)
        dr_max = min(bio_dr_max, mem_dr_max)
        metrics['DR_total'] = max(0, dr_max - dr_min)
        
        # Долговечность (минимум)
        metrics['HL_total'] = min(bio.get('HL', 0), immob.get('HL', 0), mem.get('HL', 0))
        
        # Энергопотребление (сумма)
        metrics['PC_total'] = bio.get('PC', 0) + immob.get('PC', 0) + mem.get('PC', 0)
        
        return metrics
    
    @staticmethod
    def _calculate_score(metrics: Dict[str, float]) -> float:
        """
        Расчёт итогового Score (0-10) на основе нормализованных метрик.
        
        Вес метрик:
        - SN: чувствительность (важнейшая)
        - RP: воспроизводимость
        - ST: стабильность
        - HL: долговечность
        - TR, LOD, PC: штраф за плохие значения
        """
        normalizer = MetricsNormalizer()
        
        weights = {
            'SN': 2.0,   # Максимально важная
            'RP': 1.5,   # Важная
            'ST': 1.0,   # Умеренно важная
            'HL': 1.0,   # Умеренно важная
            'DR': 1.0,   # Умеренно важная
            'TR': -0.5,  # Штраф за время отклика
            'LOD': -0.5, # Штраф за LOD
            'PC': -0.3,  # Штраф за энергопотребление
        }
        
        total_weight = sum(abs(w) for w in weights.values())
        score = 0.0
        
        for metric_name, weight in weights.items():
            value = metrics.get(f'{metric_name}_total', 0)
            normalized = normalizer.normalize(value, metric_name)
            score += normalized * weight
        
        # Шкала 0-10, нормализованная по весам
        final_score = (score / total_weight) * 10.0
        return max(0.0, min(10.0, final_score))
