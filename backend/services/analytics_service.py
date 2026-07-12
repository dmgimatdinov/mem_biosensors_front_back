# services/analytics_service.py

import os
from typing import Any, Dict, List, Optional, Tuple

from db.manager import DatabaseManager
from domain.analytics import (
    StabilityAnalysis,
    ahp_calculate_weights,
    ahp_check_consistency,
    calculate_score as calculate_mcda_score,
    epsilon_constraints_optimize,
    pareto_frontier,
    topsis_rank,
)
from domain.table_config import TABLE_CONFIGS


class AnalyticsService:
    """Сервис для аналитики и статистики БД."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.mcda_method = os.getenv("MCDA_METHOD", "weighted_sum").strip().lower() or "weighted_sum"
        self.stability_analysis = StabilityAnalysis()

    def get_statistics(self) -> Dict[str, Any]:
        return self.get_database_statistics()
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Получить статистику по всем таблицам."""
        stats = {}
        table_specs = [
            ("Analytes", "list_all_analytes"),
            ("BioRecognitionLayers", "list_all_bio_recognition_layers"),
            ("ImmobilizationLayers", "list_all_immobilization_layers"),
            ("MemristiveLayers", "list_all_memristive_layers"),
            ("SensorCombinations", "list_all_sensor_combinations"),
        ]

        for table_name, method_name in table_specs:
            fetch_method = getattr(self.db, method_name, None)
            if fetch_method:
                try:
                    data = fetch_method()
                    stats[table_name] = {
                        'label': table_name,
                        'count': len(data) if data else 0,
                    }
                except Exception as e:
                    stats[table_name] = {'label': table_name, 'count': 0, 'error': str(e)}
        
        return stats
    
    def get_best_combinations(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Получить лучшие комбинации по Score."""
        all_combos = self.db.list_all_sensor_combinations()
        if not all_combos:
            return []
        
        # Сортировка по Score (по убыванию)
        sorted_combos = sorted(
            all_combos,
            key=lambda x: x.get('Score', 0),
            reverse=True
        )
        
        return sorted_combos[:limit]
    
    def get_comparative_analysis(self) -> Dict[str, Any]:
        """Получить сравнительный анализ всех компонентов."""
        return {
            'analytes': self.db.list_all_analytes()[:3],
            'bio_layers': self.db.list_all_bio_recognition_layers()[:3],
            'immob_layers': self.db.list_all_immobilization_layers()[:3],
            'mem_layers': self.db.list_all_memristive_layers()[:3],
        }

    def calculate_score(self, structures: Any, method: Optional[str] = None, **kwargs: Any) -> Any:
        method_name = (method or kwargs.get("method") or self.mcda_method or "weighted_sum").lower()
        return calculate_mcda_score(structures, method=method_name, **kwargs)

    def calculate_ahp_weights(self, matrix: List[List[float]]) -> Dict[str, Any]:
        weights = ahp_calculate_weights(matrix)
        ci, cr, is_consistent = ahp_check_consistency(matrix)
        return {"weights": weights, "CI": ci, "CR": cr, "is_consistent": is_consistent}

    def calculate_pareto_frontier(self, structures: List[Dict[str, Any]], criteria: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        criteria = criteria or ["LoD", "ST"]
        return pareto_frontier(structures, criteria)

    def calculate_topsis(self, structures: List[Dict[str, Any]], criteria: Optional[List[str]] = None, weights: Optional[List[float]] = None) -> List[Tuple[Dict[str, Any], float]]:
        criteria = criteria or ["SN", "TR", "ST", "RP"]
        weights = weights or [0.4, 0.2, 0.2, 0.2]
        return topsis_rank(structures, criteria, weights)

    def calculate_epsilon_constraints(self, structures: List[Dict[str, Any]], objective: str, constraints: Optional[Dict[str, Tuple[str, float]]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return epsilon_constraints_optimize(structures, objective, constraints, limit)

    def run_stability_analysis(self, structures: List[Dict[str, Any]], weights: Optional[List[float]] = None, n_simulations: int = 1000, seed: Optional[int] = None, top_k: int = 10) -> Dict[str, Dict[str, Any]]:
        weights = weights or [0.4, 0.2, 0.2, 0.2]
        return self.stability_analysis.run(structures, weights, n_simulations=n_simulations, seed=seed, top_k=top_k)

    def sensitivity_to_uncertainty(self, structures: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        return self.stability_analysis.sensitivity_to_uncertainty(structures)
