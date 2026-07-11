import pytest

from services.combination_synthesis import CombinationSynthesisService
from tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
    make_compatible_four_layers,
    make_incompatible_four_layers,
)

pytestmark = pytest.mark.unit


class TestCombinationSynthesis:
    def test_synthesize_empty_db(self, tmp_db):
        """При пустой БД синтез возвращает 0 комбинаций."""
        service = CombinationSynthesisService(tmp_db)
        result = service.synthesize_all_combinations()
        assert result["checked"] == 0
        assert result["created"] == 0

    def test_synthesize_single_compatible_combo(self, tmp_db):
        """Один совместимый набор → одна комбинация."""
        analyte, bio, im, mem = make_compatible_four_layers()
        tmp_db.insert_analyte(analyte)
        tmp_db.insert_bio_recognition(bio)
        tmp_db.insert_immobilization(im)
        tmp_db.insert_memristive(mem)

        service = CombinationSynthesisService(tmp_db)
        result = service.synthesize_all_combinations()
        assert result["checked"] == 1
        assert result["created"] == 1

    @pytest.mark.parametrize("reason", ["ph", "temperature", "mechanical"])
    def test_incompatible_combo_rejected(self, reason, tmp_db):
        """Несовместимые слои не создают комбинацию."""
        analyte, bio, im, mem = make_incompatible_four_layers(reason)
        tmp_db.insert_analyte(analyte)
        tmp_db.insert_bio_recognition(bio)
        tmp_db.insert_immobilization(im)
        tmp_db.insert_memristive(mem)

        service = CombinationSynthesisService(tmp_db)
        result = service.synthesize_all_combinations()
        assert result["checked"] == 1
        assert result["created"] == 0

    def test_duplicate_combo_skipped(self, tmp_db):
        """Повторный синтез не создаёт дубликатов."""
        analyte, bio, im, mem = make_compatible_four_layers()
        tmp_db.insert_analyte(analyte)
        tmp_db.insert_bio_recognition(bio)
        tmp_db.insert_immobilization(im)
        tmp_db.insert_memristive(mem)

        service = CombinationSynthesisService(tmp_db)

        result1 = service.synthesize_all_combinations()
        assert result1["created"] == 1

        result2 = service.synthesize_all_combinations()
        assert result2["created"] == 0

    def test_combo_id_format(self, tmp_db):
        """Идентификатор комбинации соответствует шаблону."""
        analyte, bio, im, mem = make_compatible_four_layers()
        tmp_db.insert_analyte(analyte)
        tmp_db.insert_bio_recognition(bio)
        tmp_db.insert_immobilization(im)
        tmp_db.insert_memristive(mem)

        service = CombinationSynthesisService(tmp_db)
        service.synthesize_all_combinations()

        combos = tmp_db.get_combinations()
        assert len(combos) == 1
        combo_id = combos[0]["Combo_ID"]
        expected = f"COMBO_{analyte['ta_id']}_{bio['bre_id']}_{im['im_id']}_{mem['mem_id']}"
        assert combo_id == expected

    def test_max_combinations_limit(self, tmp_db):
        """Параметр max_combinations ограничивает обработку."""
        for i in range(5):
            tmp_db.insert_analyte(make_analyte(ta_id=f"TA_TEST{i:03d}"))

        tmp_db.insert_bio_recognition(make_bio_recognition_layer())
        tmp_db.insert_immobilization(make_immobilization_layer())
        tmp_db.insert_memristive(make_memristive_layer())

        service = CombinationSynthesisService(tmp_db)
        result = service.synthesize_all_combinations(max_combinations=3)
        assert result["checked"] <= 3
