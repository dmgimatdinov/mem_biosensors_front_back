import pytest

@pytest.mark.integration
class TestCombinationsAPI:

    def test_synthesize_empty_db(self, api_client):
        """POST /api/combinations/synthesize на пустой БД → 0 комбинаций."""
        response = api_client.post("/api/combinations/synthesize")
        assert response.status_code == 200
        data = response.json()
        assert data["checked"] == 0
        assert data["created"] == 0

    def test_synthesize_with_compatible_data(self, db_with_full_passport):
        """Синтез создаёт комбинации из совместимых слоёв."""
        response = db_with_full_passport.post("/api/combinations/synthesize")
        assert response.status_code == 200
        data = response.json()
        assert data["created"] >= 1
        assert data["checked"] >= 1

    def test_synthesize_idempotent(self, db_with_full_passport):
        """Повторный синтез не создаёт дубликатов."""
        response1 = db_with_full_passport.post("/api/combinations/synthesize")
        created1 = response1.json()["created"]

        response2 = db_with_full_passport.post("/api/combinations/synthesize")
        created2 = response2.json()["created"]

        assert created1 >= 1
        assert created2 == 0

    def test_list_combinations(self, db_with_full_passport):
        """GET /api/combinations возвращает список с полем Score."""
        db_with_full_passport.post("/api/combinations/synthesize")

        response = db_with_full_passport.get("/api/combinations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Score" in data[0]
        assert "Combo_ID" in data[0]
        assert "TA_ID" in data[0]
        assert "BRE_ID" in data[0]
        assert "IM_ID" in data[0]
        assert "MEM_ID" in data[0]

    def test_combination_score_in_range(self, db_with_full_passport):
        """Score всех комбинаций в диапазоне [0, 10]."""
        db_with_full_passport.post("/api/combinations/synthesize")

        response = db_with_full_passport.get("/api/combinations")
        data = response.json()
        assert data
        for combo in data:
            assert 0 <= combo["Score"] <= 10

    def test_synthesize_with_limit(self, db_with_full_passport):
        """Параметр max_combinations ограничивает обработку."""
        response = db_with_full_passport.post(
            "/api/combinations/synthesize?max_combinations=1"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["checked"] <= 1
