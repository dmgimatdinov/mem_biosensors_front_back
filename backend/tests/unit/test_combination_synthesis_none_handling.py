from services.combination_synthesis import CombinationSynthesisService
from domain.validators import CombinationValidator
from db.manager import get_connection


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


def test_delete_sensor_combinations_only_removes_test_marked_rows(tmp_db):
    tmp_db.insert_analyte({"TA_ID": "TA_1", "TA_Name": "A1", "PH_Min": 3.0, "PH_Max": 8.0, "T_Max": 40.0, "ST": 1.0})
    tmp_db.insert_analyte({"TA_ID": "TA_2", "TA_Name": "A2", "PH_Min": 3.0, "PH_Max": 8.0, "T_Max": 40.0, "ST": 1.0})
    tmp_db.insert_bio_recognition_layer({"BRE_ID": "BRE_1", "BRE_Name": "B1", "PH_Min": 3.0, "PH_Max": 8.0, "T_Min": 10.0, "T_Max": 40.0, "SN": 1.0})
    tmp_db.insert_bio_recognition_layer({"BRE_ID": "BRE_2", "BRE_Name": "B2", "PH_Min": 3.0, "PH_Max": 8.0, "T_Min": 10.0, "T_Max": 40.0, "SN": 1.0})
    tmp_db.insert_immobilization_layer({"IM_ID": "IM_1", "IM_Name": "I1", "PH_Min": 3.0, "PH_Max": 8.0, "T_Min": 10.0, "T_Max": 40.0, "MP": 100.0})
    tmp_db.insert_immobilization_layer({"IM_ID": "IM_2", "IM_Name": "I2", "PH_Min": 3.0, "PH_Max": 8.0, "T_Min": 10.0, "T_Max": 40.0, "MP": 100.0})
    tmp_db.insert_memristive_layer({"MEM_ID": "MEM_1", "MEM_Name": "M1", "PH_Min": 3.0, "PH_Max": 8.0, "T_Min": 10.0, "T_Max": 40.0, "SN": 1.0})
    tmp_db.insert_memristive_layer({"MEM_ID": "MEM_2", "MEM_Name": "M2", "PH_Min": 3.0, "PH_Max": 8.0, "T_Min": 10.0, "T_Max": 40.0, "SN": 1.0})

    tmp_db.insert_sensor_combination({
        "Combo_ID": "COMBO_TEST_1",
        "TA_ID": "TA_1",
        "BRE_ID": "BRE_1",
        "IM_ID": "IM_1",
        "MEM_ID": "MEM_1",
        "Score": 1.0,
    })
    tmp_db.insert_sensor_combination({
        "Combo_ID": "COMBO_SAFE_1",
        "TA_ID": "TA_2",
        "BRE_ID": "BRE_2",
        "IM_ID": "IM_2",
        "MEM_ID": "MEM_2",
        "Score": 2.0,
    })

    deleted = tmp_db.delete_sensor_combinations(combo_ids=["COMBO_TEST_1", "COMBO_SAFE_1"], only_test=True)

    assert deleted == 1
    remaining = tmp_db.get_combinations()
    assert [row["Combo_ID"] for row in remaining] == ["COMBO_SAFE_1"]
