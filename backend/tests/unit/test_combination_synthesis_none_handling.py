from services.combination_synthesis import CombinationSynthesisService
from domain.validators import CombinationValidator


class DummyDB:
    def __init__(self, records):
        self.records = records

    def list_all_analytes(self):
        return self.records["analytes"]

    def list_all_bio_recognition_layers(self):
        return self.records["bio_layers"]

    def list_all_immobilization_layers(self):
        return self.records["immob_layers"]

    def list_all_memristive_layers(self):
        return self.records["mem_layers"]


def test_check_ph_compatibility_skips_missing_values():
    ok, msg = CombinationValidator.check_ph_compatibility(None, 7.0, (3.0, 4.0))
    assert ok is True
    assert msg is None


def test_check_mechanical_compatibility_skips_missing_values():
    ok, msg = CombinationValidator.check_mechanical_compatibility(None, 100.0)
    assert ok is True
    assert msg is None


def test_calculate_score_handles_none_metrics():
    metrics = {
        "SN_total": None,
        "RP_total": None,
        "ST_total": None,
        "HL_total": None,
        "DR_total": None,
        "TR_total": None,
        "LOD_total": None,
        "PC_total": None,
    }
    score = CombinationSynthesisService._calculate_score(metrics)
    assert 0.0 <= score <= 10.0


def test_synthesize_all_combinations_skips_test_records(monkeypatch):
    records = {
        "analytes": [{"TA_ID": "TA_TEST001", "is_test": 1}],
        "bio_layers": [{"BRE_ID": "BRE_001"}],
        "immob_layers": [{"IM_ID": "IM_001"}],
        "mem_layers": [{"MEM_ID": "MEM_001"}],
    }
    db = DummyDB(records)
    service = CombinationSynthesisService(db)

    called = []

    def fake_create_combination(*args, **kwargs):
        called.append(args)
        return True

    monkeypatch.setattr(service, "create_combination", fake_create_combination)

    result = service.synthesize_all_combinations(max_combinations=10)

    assert result == {"checked": 0, "created": 0}
    assert called == []


def test_synthesize_all_combinations_v2_skips_test_records(monkeypatch):
    records = {
        "analytes": [{"TA_ID": "TA_TEST001", "is_test": 1}],
        "bio_layers": [{"BRE_ID": "BRE_001"}],
        "immob_layers": [{"IM_ID": "IM_001"}],
        "mem_layers": [{"MEM_ID": "MEM_001"}],
    }
    db = DummyDB(records)
    service = CombinationSynthesisService(db)

    called = []

    def fake_create_combination_v2(*args, **kwargs):
        called.append(args)
        return True

    monkeypatch.setattr(service, "create_combination_v2", fake_create_combination_v2)

    result = service.synthesize_all_combinations_v2(max_combinations=10)

    assert result == {"checked": 0, "created": 0}
    assert called == []
