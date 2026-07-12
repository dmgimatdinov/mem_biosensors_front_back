# services/combination_synthesis.py

from db.manager import DatabaseManager, TableConfig
from domain.validators import CombinationValidator
from domain.compatibility import CompatibilityEngineV2
from domain.metrics import (
    MetricsNormalizer,
    calculate_combination_metrics,
    calculate_final_score,
    calculate_reliability_coefficient,
    infer_reliability_inputs,
)
from domain.models import SensorCombination
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class CombinationSynthesisService:
    """Синтез и оценка комбинаций сенсоров."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.compatibility_v2 = CompatibilityEngineV2()
    
    def synthesize_all_combinations(self, max_combinations: int = 10000) -> Dict[str, int]:
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
                            return {"checked": total_checked, "created": successfully_created}
                        
                        total_checked += 1
                        
                        try:
                            result = self.create_combination(
                                analyte, bio_layer, immob_layer, mem_layer
                            )
                            if result:
                                successfully_created += 1
                        except Exception:
                            logger.exception("Ошибка при создании комбинации")
        
        logger.info(f"Синтез завершён: {total_checked} проверено, {successfully_created} создано")
        return {"checked": total_checked, "created": successfully_created}
    
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
        analyte = self._normalize_record(analyte, "analyte")
        bio_layer = self._normalize_record(bio_layer, "bio")
        immob_layer = self._normalize_record(immob_layer, "immob")
        mem_layer = self._normalize_record(mem_layer, "mem")

        # Валидация совместимости
        is_valid, error_msg = CombinationValidator.validate_combination(
            analyte, bio_layer, immob_layer, mem_layer
        )
        if not is_valid:
            logger.debug(f"Комбинация {analyte.get('TA_ID', analyte.get('ta_id'))}-{bio_layer.get('BRE_ID', bio_layer.get('bre_id'))}-{immob_layer.get('IM_ID', immob_layer.get('im_id'))}-{mem_layer.get('MEM_ID', mem_layer.get('mem_id'))}: {error_msg}")
            return False

        # Расчёт интегральных метрик
        metrics = self._calculate_metrics(analyte, bio_layer, immob_layer, mem_layer)

        # Расчёт базового Score
        raw_score = self._calculate_score(metrics)
        eta, alpha, gamma = infer_reliability_inputs({
            'analyte': analyte,
            'bio_layer': bio_layer,
            'immobilization_layer': immob_layer,
            'memristive_layer': mem_layer,
            **metrics,
        })
        kappa = calculate_reliability_coefficient(eta=eta, alpha=alpha, gamma=gamma)
        score = max(0.0, min(10.0, calculate_final_score(raw_score, kappa)))

        # ID комбинации
        combo_id = f"COMBO_{analyte.get('TA_ID', analyte.get('ta_id'))}_{bio_layer.get('BRE_ID', bio_layer.get('bre_id'))}_{immob_layer.get('IM_ID', immob_layer.get('im_id'))}_{mem_layer.get('MEM_ID', mem_layer.get('mem_id'))}"

        # Подготовка данных для БД
        combination_data = {
            'Combo_ID': combo_id,
            'TA_ID': analyte.get('TA_ID', analyte.get('ta_id')),
            'BRE_ID': bio_layer.get('BRE_ID', bio_layer.get('bre_id')),
            'IM_ID': immob_layer.get('IM_ID', immob_layer.get('im_id')),
            'MEM_ID': mem_layer.get('MEM_ID', mem_layer.get('mem_id')),
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
            logger.info(
                f"✅ Комбинация {combo_id} создана "
                f"(raw={raw_score:.3f}, kappa={kappa:.3f}, score={score:.3f})"
            )
            return True
        elif result == "DUPLICATE":
            logger.debug(f"⚠️ Комбинация {combo_id} уже существует")
            return False
        else:
            logger.error(f"❌ Ошибка при добавлении комбинации {combo_id}")
            return False

    def create_combination_v2(
        self,
        analyte: Dict[str, Any],
        bio_layer: Dict[str, Any],
        immob_layer: Dict[str, Any],
        mem_layer: Dict[str, Any],
        application_profile: str = "PoC",
    ) -> bool:
        """Создание комбинации через новый CompatibilityEngineV2."""
        analyte = self._normalize_record(analyte, "analyte")
        bio_layer = self._normalize_record(bio_layer, "bio")
        immob_layer = self._normalize_record(immob_layer, "immob")
        mem_layer = self._normalize_record(mem_layer, "mem")

        structure = {
            "analyte": analyte,
            "bio_layer": bio_layer,
            "immobilization_layer": immob_layer,
            "memristive_layer": mem_layer,
            "iso_10993": True,
            "temperature_resistant": True,
        }

        stage1_ok, stage1_failed = self.compatibility_v2.validate_stage1(structure)
        if not stage1_ok:
            logger.debug(f"V2 Stage1 failed: {stage1_failed}")
            return False

        metrics = self._calculate_metrics(analyte, bio_layer, immob_layer, mem_layer)
        structure.update(metrics)
        structure["PC_total"] = metrics.get("PC_total", 0)
        structure["TR_total"] = metrics.get("TR_total", 0)
        structure["ST_total"] = metrics.get("ST_total", 0)

        stage2_ok, stage2_failed = self.compatibility_v2.validate_stage2(structure, application_profile)
        if not stage2_ok:
            logger.debug(f"V2 Stage2 failed: {stage2_failed}")
            return False

        raw_score = self._calculate_score(metrics)
        eta, alpha, gamma = infer_reliability_inputs({
            'analyte': analyte,
            'bio_layer': bio_layer,
            'immobilization_layer': immob_layer,
            'memristive_layer': mem_layer,
            **metrics,
        })
        kappa = calculate_reliability_coefficient(eta=eta, alpha=alpha, gamma=gamma)
        score = max(0.0, min(10.0, calculate_final_score(raw_score, kappa)))

        combo_id = (
            f"COMBO_{analyte.get('TA_ID', analyte.get('ta_id'))}_"
            f"{bio_layer.get('BRE_ID', bio_layer.get('bre_id'))}_"
            f"{immob_layer.get('IM_ID', immob_layer.get('im_id'))}_"
            f"{mem_layer.get('MEM_ID', mem_layer.get('mem_id'))}"
        )

        combination_data = {
            'Combo_ID': combo_id,
            'TA_ID': analyte.get('TA_ID', analyte.get('ta_id')),
            'BRE_ID': bio_layer.get('BRE_ID', bio_layer.get('bre_id')),
            'IM_ID': immob_layer.get('IM_ID', immob_layer.get('im_id')),
            'MEM_ID': mem_layer.get('MEM_ID', mem_layer.get('mem_id')),
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
        return result is True

    def synthesize_all_combinations_v2(
        self,
        max_combinations: int = 10000,
        application_profile: str = "PoC",
    ) -> Dict[str, int]:
        """Синтез комбинаций через CompatibilityEngineV2."""
        analytes = self.db.list_all_analytes()
        bio_layers = self.db.list_all_bio_recognition_layers()
        immob_layers = self.db.list_all_immobilization_layers()
        mem_layers = self.db.list_all_memristive_layers()

        total_checked = 0
        successfully_created = 0

        for analyte in analytes:
            for bio_layer in bio_layers:
                for immob_layer in immob_layers:
                    for mem_layer in mem_layers:
                        if total_checked >= max_combinations:
                            return {"checked": total_checked, "created": successfully_created}

                        total_checked += 1
                        try:
                            if self.create_combination_v2(
                                analyte,
                                bio_layer,
                                immob_layer,
                                mem_layer,
                                application_profile=application_profile,
                            ):
                                successfully_created += 1
                        except Exception:
                            logger.exception("Ошибка при создании комбинации v2")

        return {"checked": total_checked, "created": successfully_created}
    
    @staticmethod
    def _normalize_record(record: Dict[str, Any], kind: str) -> Dict[str, Any]:
        normalized = dict(record)

        aliases = {
            "analyte": {
                "TA_ID": "ta_id",
                "TA_Name": "ta_name",
                "PH_Min": "ph_min",
                "PH_Max": "ph_max",
                "T_Max": "t_max",
                "ST": "stability",
                "HL": "half_life",
                "PC": "power_consumption",
            },
            "bio": {
                "BRE_ID": "bre_id",
                "BRE_Name": "bre_name",
                "PH_Min": "ph_min",
                "PH_Max": "ph_max",
                "T_Min": "t_min",
                "T_Max": "t_max",
                "SN": "sensitivity",
                "DR_Min": "dr_min",
                "DR_Max": "dr_max",
                "RP": "reproducibility",
                "TR": "response_time",
                "ST": "stability",
                "LOD": "lod",
                "HL": "durability",
                "PC": "power_consumption",
            },
            "immob": {
                "IM_ID": "im_id",
                "IM_Name": "im_name",
                "PH_Min": "ph_min",
                "PH_Max": "ph_max",
                "T_Min": "t_min",
                "T_Max": "t_max",
                "MP": "young_modulus",
                "Adh": "adhesion",
                "Sol": "solubility",
                "K_IM": "loss_coefficient",
                "RP": "reproducibility",
                "TR": "response_time",
                "ST": "stability",
                "HL": "durability",
                "PC": "power_consumption",
            },
            "mem": {
                "MEM_ID": "mem_id",
                "MEM_Name": "mem_name",
                "PH_Min": "ph_min",
                "PH_Max": "ph_max",
                "T_Min": "t_min",
                "T_Max": "t_max",
                "MP": "young_modulus",
                "SN": "sensitivity",
                "DR_Min": "dr_min",
                "DR_Max": "dr_max",
                "RP": "reproducibility",
                "TR": "response_time",
                "ST": "stability",
                "LOD": "lod",
                "HL": "durability",
                "PC": "power_consumption",
            },
        }
        mapping = aliases.get(kind, {})
        for upper, lower in mapping.items():
            if upper not in normalized and lower in normalized:
                normalized[upper] = normalized[lower]
            if lower not in normalized and upper in normalized:
                normalized[lower] = normalized[upper]
        return normalized

    @staticmethod
    def _calculate_metrics(
        analyte: Dict, bio: Dict, immob: Dict, mem: Dict
    ) -> Dict[str, float]:
        """Расчёт интегральных характеристик комбинации через фасад версий метрик."""
        return calculate_combination_metrics(analyte, bio, immob, mem)
    
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
            raw_value = metrics.get(f'{metric_name}_total', 0)
            if raw_value is None:
                raw_value = 0.0
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                value = 0.0
            normalized = normalizer.normalize(value, metric_name)
            score += normalized * weight
        
        # Шкала 0-10, нормализованная по весам
        final_score = (score / total_weight) * 10.0
        return max(0.0, min(10.0, final_score))
