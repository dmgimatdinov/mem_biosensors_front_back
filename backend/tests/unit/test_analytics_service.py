import pytest

from services.analytics_service import AnalyticsService
from tests.factories import make_analyte

pytestmark = pytest.mark.unit


class TestAnalyticsService:
    def test_statistics_empty_db(self, tmp_db):
        """Статистика для пустой БД возвращает нули."""
        service = AnalyticsService(tmp_db)
        stats = service.get_statistics()
        assert len(stats) == 5  # 5 таблиц
        for table_stats in stats.values():
            assert table_stats["count"] == 0

    def test_statistics_with_data(self, tmp_db):
        """Статистика корректно считает записи."""
        tmp_db.insert_analyte(make_analyte(ta_id="TA_TEST001"))
        tmp_db.insert_analyte(make_analyte(ta_id="TA_TEST002"))

        service = AnalyticsService(tmp_db)
        stats = service.get_statistics()
        assert stats["Analytes"]["count"] == 2

    def test_best_combinations_sorted(self, tmp_db):
        """Лучшие комбинации отсортированы по убыванию Score."""
        for score in [1.0, 5.0, 3.0]:
            tmp_db.insert_sensor_combination(
                {
                    "Combo_ID": f"COMBO_{score}",
                    "TA_ID": "TA_TEST001",
                    "BRE_ID": "BRE_TEST001",
                    "IM_ID": "IM_TEST001",
                    "MEM_ID": "MEM_TEST001",
                    "Score": score,
                }
            )

        service = AnalyticsService(tmp_db)
        best = service.get_best_combinations(limit=10)
        scores = [combo["Score"] for combo in best]
        assert scores == sorted(scores, reverse=True)
