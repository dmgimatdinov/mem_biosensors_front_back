# services/analytics_service.py

from db.manager import DatabaseManager
from typing import Dict, Any
from domain.table_config import TABLE_CONFIGS

class AnalyticsService:
    """Сервис для аналитики и статистики БД."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db

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
