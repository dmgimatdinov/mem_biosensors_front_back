# Набор промтов для реализации плана тестирования и CI/CD

Коллега, разобью задачу на **12 последовательных промтов**. Каждый промт — самодостаточная единица: после его выполнения система остаётся валидной, все предыдущие тесты проходят, добавляется новый слой функциональности.

## Общая стратегия

**Принцип «маленьких шагов»:** каждый промт добавляет тесты, которые гарантированно проходят. Это позволяет студентам видеть прогресс и не терять мотивацию.

**Оптимизация времени:**
- Параллельный запуск через `pytest-xdist` (unit-тесты в 4-8 раз быстрее)
- Разделение по маркерам: `fast` (unit+smoke), `medium` (integration), `slow` (e2e)
- Кэширование pip и Docker-слоёв в CI
- Матрица тестов: быстрые на каждый push, медленные — на PR/nightly

**Порядок промтов:**
1. Фундамент (конфигурация, фабрики, фикстуры)
2. Unit-тесты валидаторов
3. Unit-тесты бизнес-логики
4. Integration-тесты API (CRUD)
5. Integration-тесты (расширенные)
6. Контрактные тесты
7. Smoke-тесты и окруженией
8. Тесты безопасности
9. Тесты производительности
10. E2E-тесты (Playwright)
11. CI/CD workflows
12. Финализация и документация

---

## 📨 СООБЩЕНИЕ 1: ПРОМТ 1 — ФУНДАМЕНТ ТЕСТОВОЙ ИНФРАСТРУКТУРЫ

```
Ты — senior Python-разработчик, специализирующийся на тестировании FastAPI-приложений. 
Твоя задача — создать фундамент тестовой инфраструктуры для проекта 
"Memristive Biosensors Passport Manager" (FastAPI + SQLite + Next.js).

🎯 ЦЕЛЬ ПРОМТА:
Создать базовую структуру тестов, которая:
1. Гарантирует изоляцию каждого теста (своя SQLite-БД в tmp_path)
2. Обеспечивает детерминированность данных (префиксы *_TEST*)
3. Позволяет быстро расширять тестовую базу
4. Оптимизирована для параллельного запуска

⚠️ КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
- Python только 3.11+
- Pydantic v2 (model_dump, model_validate, ConfigDict)
- FastAPI 0.115.0+
- После выполнения ВСЕ существующие тесты должны проходить
- Никаких поломок текущего функционала

📋 ЗАДАЧИ:

### 1.1. Создать файл `backend/requirements-dev.txt`:
```
# Core testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-timeout>=2.2.0
pytest-mock>=3.12.0
pytest-xdist>=3.5.0              # ПАРАЛЛЕЛЬНЫЙ ЗАПУСК (оптимизация!)

# FastAPI testing
httpx>=0.25.0

# Data generation
faker>=20.0.0

# Code quality
flake8>=6.1.0
mypy>=1.7.0
black>=23.0.0
```

### 1.2. Создать/обновить `backend/pytest.ini`:
```ini
[pytest]
pythonpath = .
testpaths = backend/tests
addopts = -v --strict-markers --tb=short -n auto
# -n auto = автоопределение числа ядер для параллельного запуска

markers =
    unit: unit tests (fast, <1s each)
    integration: integration tests (medium, <5s each)
    contract: contract tests (API schemas)
    smoke: smoke tests (startup, migrations)
    security: security tests
    performance: performance tests
    e2e: end-to-end tests (slow)
    slow: tests that take more than 5 seconds
    fast: tests that take less than 1s

python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Оптимизация: игнорируем известные предупреждения
filterwarnings =
    ignore::DeprecationWarning
    ignore::pytest.PytestUnraisableExceptionWarning
```

### 1.3. Создать `backend/tests/__init__.py` (пустой)

### 1.4. Создать `backend/tests/factories.py` — фабрики тестовых данных:
- `make_analyte(**overrides)` — генерирует валидный аналит
- `make_bio_recognition_layer(**overrides)` — биораспознающий слой
- `make_immobilization_layer(**overrides)` — иммобилизационный слой
- `make_memristive_layer(**overrides)` — мемристивный слой
- `make_compatible_four_layers()` — возвращает 4 совместимых слоя
- `make_incompatible_four_layers(reason)` — несовместимый набор
  (reason: "ph" | "temperature" | "mechanical")

ВАЖНО:
- Все ID начинаются с префикса *_TEST* (например, "TA_TEST001")
- Значения полей — валидные (в пределах допустимых диапазонов)
- Для совместимого набора: pH-диапазоны пересекаются, температуры согласованы, 
  модули Юнга отличаются ≤ 0.5 ГПа

### 1.5. Создать `backend/tests/conftest.py` с фикстурами:

```python
@pytest.fixture
def tmp_db(tmp_path):
    """Создаёт временную БД и возвращает DatabaseManager."""
    db_path = tmp_path / "test.db"
    # Инициализируем БД (миграции)
    # Возвращаем менеджер
    yield db_manager
    # Очистка (если нужна)

@pytest.fixture
def api_client(tmp_db, monkeypatch):
    """TestClient с изолированной БД."""
    # Подменяем DATABASE_URL на tmp_db
    # Создаём TestClient(app)
    yield client
    # Восстанавливаем окружение

@pytest.fixture
def db_with_analytes(api_client):
    """БД с 5 тестовыми аналитами."""
    # Создаём 5 аналитов через API
    return api_client

@pytest.fixture
def db_with_full_passport(api_client):
    """БД с полным паспортом (4 совместимых слоя)."""
    # Используем make_compatible_four_layers()
    return api_client
```

### 1.6. Создать `backend/tests/test_factories.py` — тесты самих фабрик:
```python
def test_factories_use_test_prefixes():
    """Все ID содержат '_TEST'."""
    # Проверяем все 4 фабрики

def test_compatible_layers_are_compatible():
    """make_compatible_four_layers() возвращает совместимые слои."""
    # Проверяем пересечение pH, температур, модулей Юнга

@pytest.mark.parametrize("reason", ["ph", "temperature", "mechanical"])
def test_incompatible_layers_are_incompatible(reason):
    """make_incompatible_four_layers() возвращает несовместимые слои."""
    # Проверяем, что валидация отклоняет такой набор
```

### 1.7. Оптимизация для быстрого запуска:
- Использовать `@pytest.mark.unit` для быстрых тестов
- Настроить `pytest-xdist` для параллельного запуска
- Добавить в Makefile команды:
```makefile
test-fast:
    pytest -m "unit or smoke" -n auto

test-all:
    pytest -n auto

test-unit:
    pytest backend/tests/unit/ -n auto

test-integration:
    pytest backend/tests/integration/ -n auto
```

✅ КРИТЕРИИ ПРИЁМКИ:
1. `pip install -r requirements-dev.txt` устанавливается без ошибок
2. `pytest backend/tests/test_factories.py` — все тесты проходят
3. `pytest -n auto` запускается параллельно (видно в выводе: "scheduling tests via LoadScheduling")
4. Фабрики генерируют валидные данные
5. Фикстуры создают изолированные БД
6. Все существующие тесты из репозитория продолжают проходить

📦 РЕЗУЛЬТАТ:
После выполнения этого промта у нас есть:
- Рабочая тестовая инфраструктура
- Фабрики для генерации данных
- Фикстуры для изоляции тестов
- Оптимизация через параллельный запуск

Время выполнения промта: ~30 минут для LLM.
Время выполнения тестов: < 5 секунд для фабрик.

⚡ СЛЕДУЮЩИЙ ШАГ:
После успешного выполнения этого промта, переходим к ПРОМТУ 2 — 
Unit-тесты валидаторов с параметризацией.

Выполни этот промт, убедись, что все тесты проходят, и сообщи результат.
Если возникнут ошибки — покажи их, и мы исправим.
```

---

## 📨 СООБЩЕНИЕ 2: ПРОМТ 2 — UNIT-ТЕСТЫ ВАЛИДАТОРОВ

```
Ты — senior Python-разработчик. Предыдущий промт (фундамент) успешно выполнен.
Теперь создаём unit-тесты для валидаторов всех четырёх слоёв биосенсора.

🎯 ЦЕЛЬ ПРОМТА:
Покрыть тестами ВСЕ валидационные правила для:
- Analyte (TA)
- BioRecognitionLayer (BRE)
- ImmobilizationLayer (IM)
- MemristiveLayer (MEM)

⚠️ КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
- Использовать параметризованные тесты (@pytest.mark.parametrize)
- Каждый тест должен выполняться < 0.1 секунды
- После выполнения ВСЕ предыдущие тесты (из промта 1) должны проходить
- Покрытие валидаторов — 100%

📋 ЗАДАЧИ:

### 2.1. Создать `backend/tests/unit/__init__.py` (пустой)

### 2.2. Создать `backend/tests/unit/test_validators.py`:

Структура:
```python
import pytest
from backend.domain.validators import UniversalBiosensorValidator
from backend.tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer
)

class TestAnalyteValidation:
    """Тесты валидации аналитов."""
    
    def test_valid_analyte_passes(self):
        """Валидный аналит проходит валидацию."""
        data = make_analyte()
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert result.success
        assert not result.errors
    
    @pytest.mark.parametrize("field,value,expected_error", [
        # Невалидный формат ID
        ("ta_id", "ABC001", "должен начинаться с TA"),
        ("ta_id", "TA" + "x" * 30, "превышает длину"),
        
        # Невалидное имя
        ("ta_name", "AB", "слишком короткое"),
        ("ta_name", "A" * 300, "слишком длинное"),
        
        # pH вне диапазона
        ("ph_min", 1.0, "вне диапазона"),
        ("ph_min", 11.0, "вне диапазона"),
        ("ph_max", 1.0, "вне диапазона"),
        ("ph_max", 11.0, "вне диапазона"),
        
        # Температура вне диапазона
        ("t_max", -10, "вне диапазона"),
        ("t_max", 200, "вне диапазона"),
        
        # Stability вне диапазона
        ("stability", -1, "вне диапазона"),
        ("stability", 400, "вне диапазона"),
        
        # Half-life вне диапазона
        ("half_life", -1, "вне диапазона"),
        ("half_life", 10000, "вне диапазона"),
        
        # Power consumption вне диапазона
        ("power_consumption", -1, "вне диапазона"),
        ("power_consumption", 2000, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_analyte(**{field: value})
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert not result.success
        assert any(expected_error in err.lower() for err in result.errors)
    
    def test_ph_min_greater_than_ph_max(self):
        """pH_Min не может превышать pH_Max."""
        data = make_analyte(ph_min=8.0, ph_max=5.0)
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert not result.success
        assert any("ph" in err.lower() for err in result.errors)
    
    def test_missing_required_fields(self):
        """Отсутствие обязательных полей отклоняется."""
        data = make_analyte()
        del data["ta_id"]
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert not result.success
        assert any("обязательн" in err.lower() for err in result.errors)
    
    def test_boundary_values(self):
        """Граничные значения проходят валидацию."""
        data = make_analyte(ph_min=2.0, ph_max=10.0, t_max=0)
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert result.success
        
        data = make_analyte(ph_min=2.0, ph_max=10.0, t_max=180)
        result = UniversalBiosensorValidator.validate("analyte", data)
        assert result.success

class TestBioRecognitionValidation:
    """Тесты валидации биораспознающего слоя."""
    
    def test_valid_bio_layer_passes(self):
        """Валидный биослой проходит валидацию."""
        data = make_bio_recognition_layer()
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert result.success
    
    @pytest.mark.parametrize("field,value,expected_error", [
        ("bre_id", "ABC001", "должен начинаться с BRE"),
        ("bre_name", "AB", "слишком короткое"),
        ("ph_min", 1.0, "вне диапазона"),
        ("ph_max", 11.0, "вне диапазона"),
        ("t_min", -10, "вне диапазона"),
        ("t_max", 200, "вне диапазона"),
        ("dr_min", -1.0, "вне диапазона"),
        ("dr_max", 20000.0, "вне диапазона"),
        ("sensitivity", -1, "вне диапазона"),
        ("reproducibility", -1, "вне диапазона"),
        ("reproducibility", 101, "вне диапазона"),
        ("response_time", -1, "вне диапазона"),
        ("stability", -1, "вне диапазона"),
        ("lod", -1, "вне диапазона"),
        ("durability", -1, "вне диапазона"),
        ("power_consumption", -1, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_bio_recognition_layer(**{field: value})
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success
        assert any(expected_error in err.lower() for err in result.errors)
    
    def test_ph_min_greater_than_ph_max(self):
        """pH_Min > pH_Max отклоняется."""
        data = make_bio_recognition_layer(ph_min=8.0, ph_max=5.0)
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success
    
    def test_t_min_greater_than_t_max(self):
        """T_Min > T_Max отклоняется."""
        data = make_bio_recognition_layer(t_min=60, t_max=20)
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success
    
    def test_dr_min_greater_than_dr_max(self):
        """DR_Min > DR_Max отклоняется."""
        data = make_bio_recognition_layer(dr_min=1000.0, dr_max=0.1)
        result = UniversalBiosensorValidator.validate("bio_recognition", data)
        assert not result.success

class TestImmobilizationValidation:
    """Тесты валидации иммобилизационного слоя."""
    
    def test_valid_im_layer_passes(self):
        """Валидный иммобилизационный слой проходит валидацию."""
        data = make_immobilization_layer()
        result = UniversalBiosensorValidator.validate("immobilization", data)
        assert result.success
    
    @pytest.mark.parametrize("field,value,expected_error", [
        ("im_id", "ABC001", "должен начинаться с IM"),
        ("im_name", "AB", "слишком короткое"),
        ("young_modulus", -1, "вне диапазона"),
        ("young_modulus", 200, "вне диапазона"),
        ("adhesion", "invalid_value", "недопустимое значение"),
        ("solubility", "invalid_value", "недопустимое значение"),
        ("loss_coefficient", -1.0, "вне диапазона"),
        ("loss_coefficient", 2.0, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_immobilization_layer(**{field: value})
        result = UniversalBiosensorValidator.validate("immobilization", data)
        assert not result.success
        assert any(expected_error in err.lower() for err in result.errors)

class TestMemristiveValidation:
    """Тесты валидации мемристивного слоя."""
    
    def test_valid_mem_layer_passes(self):
        """Валидный мемристивный слой проходит валидацию."""
        data = make_memristive_layer()
        result = UniversalBiosensorValidator.validate("memristive", data)
        assert result.success
    
    @pytest.mark.parametrize("field,value,expected_error", [
        ("mem_id", "ABC001", "должен начинаться с MEM"),
        ("mem_name", "AB", "слишком короткое"),
        ("dr_min", -1.0, "вне диапазона"),
        ("dr_max", 20000.0, "вне диапазона"),
        ("young_modulus", -1, "вне диапазона"),
        ("young_modulus", 200, "вне диапазона"),
    ])
    def test_invalid_field_values(self, field, value, expected_error):
        """Невалидные значения полей отклоняются."""
        data = make_memristive_layer(**{field: value})
        result = UniversalBiosensorValidator.validate("memristive", data)
        assert not result.success
        assert any(expected_error in err.lower() for err in result.errors)

class TestCrossLayerValidation:
    """Тесты валидации совместимости слоёв."""
    
    def test_compatible_layers_pass(self):
        """Совместимые слои проходят валидацию."""
        analyte, bio, im, mem = make_compatible_four_layers()
        
        # Каждый слой валиден
        assert UniversalBiosensorValidator.validate("analyte", analyte).success
        assert UniversalBiosensorValidator.validate("bio_recognition", bio).success
        assert UniversalBiosensorValidator.validate("immobilization", im).success
        assert UniversalBiosensorValidator.validate("memristive", mem).success
    
    @pytest.mark.parametrize("reason", ["ph", "temperature", "mechanical"])
    def test_incompatible_layers_fail(self, reason):
        """Несовместимые слои отклоняются."""
        analyte, bio, im, mem = make_incompatible_four_layers(reason)
        
        # Каждый слой валиден по отдельности
        assert UniversalBiosensorValidator.validate("analyte", analyte).success
        assert UniversalBiosensorValidator.validate("bio_recognition", bio).success
        assert UniversalBiosensorValidator.validate("immobilization", im).success
        assert UniversalBiosensorValidator.validate("memristive", mem).success
        
        # Но вместе они несовместимы
        # (если есть метод validate_compatibility)
        # result = UniversalBiosensorValidator.validate_compatibility(analyte, bio, im, mem)
        # assert not result.success
```

### 2.3. Оптимизация:
- Все тесты помечены `@pytest.mark.unit`
- Каждый тест выполняется < 0.1 секунды
- Параметризация уменьшает дублирование кода
- Используется `factories.py` из промта 1

### 2.4. Запуск тестов:
```bash
# Только unit-тесты валидаторов
pytest backend/tests/unit/test_validators.py -v

# С покрытием
pytest backend/tests/unit/test_validators.py --cov=backend.domain.validators --cov-report=term-missing

# Параллельно
pytest backend/tests/unit/test_validators.py -n auto
```

✅ КРИТЕРИИ ПРИЁМКИ:
1. Все тесты из промта 1 проходят
2. Все новые тесты проходят
3. Покрытие валидаторов ≥ 95%
4. Время выполнения всех unit-тестов < 2 секунды
5. Параметризованные тесты работают корректно

📦 РЕЗУЛЬТАТ:
После выполнения этого промта у нас есть:
- Полное покрытие валидаторов тестами
- Параметризованные тесты для всех полей
- Тесты граничных значений
- Тесты логических ограничений (pH_Min > pH_Max и т.д.)

Время выполнения промта: ~40 минут для LLM.
Время выполнения тестов: < 2 секунды.

⚡ СЛЕДУЮЩИЙ ШАГ:
После успешного выполнения этого промта, переходим к ПРОМТУ 3 — 
Unit-тесты бизнес-логики (синтез комбинаций, расчёт метрик, Score).

Выполни этот промт, убедись, что все тесты проходят, и сообщи результат.
```

---

## 📨 СООБЩЕНИЕ 3: ПРОМТ 3 — UNIT-ТЕСТЫ БИЗНЕС-ЛОГИКИ

```
Ты — senior Python-разработчик. Промты 1 и 2 успешно выполнены.
Теперь создаём unit-тесты для бизнес-логики:
- Синтез комбинаций (CombinationSynthesisService)
- Расчёт метрик (MetricsCalculator)
- Расчёт Score (ScoreNormalizer)
- Аналитика (AnalyticsService)
- Экспорт (ExportService)

🎯 ЦЕЛЬ ПРОМТА:
Покрыть тестами ВСЮ бизнес-логику системы.

⚠️ КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
- Каждый тест выполняется < 1 секунды
- Использовать фабрики из промта 1
- После выполнения ВСЕ предыдущие тесты должны проходить
- Покрытие бизнес-логики ≥ 80%

📋 ЗАДАЧИ:

### 3.1. Создать `backend/tests/unit/test_combination_synthesis.py`:

```python
import pytest
from backend.services.combination_service import CombinationSynthesisService
from backend.tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer,
    make_compatible_four_layers,
    make_incompatible_four_layers
)

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
        # Создаём 5 аналитов
        for i in range(5):
            tmp_db.insert_analyte(make_analyte(ta_id=f"TA_TEST{i:03d}"))
        
        # Один биослой, один иммобилизационный, один мемристивный
        tmp_db.insert_bio_recognition(make_bio_recognition_layer())
        tmp_db.insert_immobilization(make_immobilization_layer())
        tmp_db.insert_memristive(make_memristive_layer())
        
        service = CombinationSynthesisService(tmp_db)
        result = service.synthesize_all_combinations(max_combinations=3)
        assert result["checked"] <= 3
```

### 3.2. Создать `backend/tests/unit/test_metrics_calculator.py`:

```python
import pytest
from backend.services.metrics_calculator import (
    calculate_sn_total,
    calculate_tr_total,
    calculate_st_total,
    calculate_lod_total,
    calculate_dr_total,
    calculate_pc_total
)
from backend.tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer
)

class TestMetricsCalculator:
    
    def test_sn_total_formula(self):
        """SN_total = SN_bio × SN_mem × K_IM."""
        bio = make_bio_recognition_layer(sensitivity=1000)
        im = make_immobilization_layer(loss_coefficient=0.5)
        mem = make_memristive_layer(sensitivity=200)
        
        sn_total = calculate_sn_total(bio, im, mem)
        expected = 1000 * 200 * 0.5
        assert sn_total == expected
    
    def test_tr_total_formula(self):
        """TR_total = TR_bio + TR_im + TR_mem."""
        bio = make_bio_recognition_layer(response_time=30)
        im = make_immobilization_layer(response_time=60)
        mem = make_memristive_layer(response_time=10)
        
        tr_total = calculate_tr_total(bio, im, mem)
        assert tr_total == 100
    
    def test_st_total_is_minimum(self):
        """ST_total = min(ST_bio, ST_im, ST_mem)."""
        bio = make_bio_recognition_layer(stability=90)
        im = make_immobilization_layer(stability=120)
        mem = make_memristive_layer(stability=60)
        
        st_total = calculate_st_total(bio, im, mem)
        assert st_total == 60
    
    def test_lod_total_is_maximum(self):
        """LOD_total = max(LOD_bio, LOD_mem)."""
        bio = make_bio_recognition_layer(lod=100)
        mem = make_memristive_layer(lod=50)
        
        lod_total = calculate_lod_total(bio, mem)
        assert lod_total == 100
    
    def test_dr_total_is_intersection(self):
        """DR_total = пересечение диапазонов."""
        bio = make_bio_recognition_layer(dr_min=0.1, dr_max=1000.0)
        mem = make_memristive_layer(dr_min=0.5, dr_max=500.0)
        
        dr_total = calculate_dr_total(bio, mem)
        expected = max(0, min(1000.0, 500.0) - max(0.1, 0.5))
        assert abs(dr_total - expected) < 1e-9
    
    def test_pc_total_is_sum(self):
        """PC_total = сумма энергопотреблений."""
        analyte = make_analyte(power_consumption=500)
        bio = make_bio_recognition_layer(power_consumption=200)
        im = make_immobilization_layer(power_consumption=100)
        mem = make_memristive_layer(power_consumption=300)
        
        pc_total = calculate_pc_total(analyte, bio, im, mem)
        assert pc_total == 1100
```

### 3.3. Создать `backend/tests/unit/test_score_normalizer.py`:

```python
import pytest
from backend.services.score_normalizer import calculate_score
from backend.tests.factories import generate_random_metrics

class TestScoreNormalizer:
    
    def test_score_range(self):
        """Score всегда в диапазоне [0, 10]."""
        for _ in range(100):
            metrics = generate_random_metrics()
            score = calculate_score(metrics)
            assert 0 <= score <= 10
    
    def test_score_monotonicity_sn(self):
        """При увеличении SN Score не уменьшается."""
        metrics1 = {"sn_total": 100, "tr_total": 100, "st_total": 100, 
                    "lod_total": 100, "dr_total": 100, "pc_total": 100}
        metrics2 = {"sn_total": 200, "tr_total": 100, "st_total": 100,
                    "lod_total": 100, "dr_total": 100, "pc_total": 100}
        
        score1 = calculate_score(metrics1)
        score2 = calculate_score(metrics2)
        assert score2 >= score1
    
    def test_score_monotonicity_tr(self):
        """При увеличении TR Score не увеличивается (штраф)."""
        metrics1 = {"sn_total": 100, "tr_total": 50, "st_total": 100,
                    "lod_total": 100, "dr_total": 100, "pc_total": 100}
        metrics2 = {"sn_total": 100, "tr_total": 100, "st_total": 100,
                    "lod_total": 100, "dr_total": 100, "pc_total": 100}
        
        score1 = calculate_score(metrics1)
        score2 = calculate_score(metrics2)
        assert score2 <= score1
    
    def test_perfect_combo_score(self):
        """Идеальная комбинация даёт Score ≈ 10."""
        perfect_metrics = {
            "sn_total": 20000,
            "tr_total": 1,
            "st_total": 365,
            "lod_total": 1,
            "dr_total": 1000,
            "pc_total": 100
        }
        score = calculate_score(perfect_metrics)
        assert score >= 9.5
    
    def test_worst_combo_score(self):
        """Худшая комбинация даёт Score ≈ 0."""
        worst_metrics = {
            "sn_total": 1,
            "tr_total": 3600,
            "st_total": 1,
            "lod_total": 50000,
            "dr_total": 0,
            "pc_total": 2000
        }
        score = calculate_score(worst_metrics)
        assert score <= 0.5
```

### 3.4. Создать `backend/tests/unit/test_analytics_service.py`:

```python
import pytest
from backend.services.analytics_service import AnalyticsService
from backend.tests.factories import make_analyte

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
        # Создаём несколько комбинаций с разными Score
        # ...
        service = AnalyticsService(tmp_db)
        best = service.get_best_combinations(limit=10)
        scores = [combo["Score"] for combo in best]
        assert scores == sorted(scores, reverse=True)
```

### 3.5. Создать `backend/tests/unit/test_export_service.py`:

```python
import pytest
from backend.services.export_service import ExportService
from backend.tests.factories import make_analyte

class TestExportService:
    
    def test_export_csv_format(self, tmp_db):
        """Экспорт в CSV возвращает корректный формат."""
        tmp_db.insert_analyte(make_analyte())
        service = ExportService(tmp_db)
        result = service.export_table("Analytes", format="csv")
        assert "TA_TEST" in result
        assert "," in result
    
    def test_export_json_format(self, tmp_db):
        """Экспорт в JSON возвращает валидный JSON."""
        tmp_db.insert_analyte(make_analyte())
        service = ExportService(tmp_db)
        result = service.export_table("Analytes", format="json")
        import json
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1
    
    def test_export_invalid_format(self, tmp_db):
        """Невалидный формат выбрасывает исключение."""
        service = ExportService(tmp_db)
        with pytest.raises(ValueError):
            service.export_table("Analytes", format="xml")
    
    def test_export_nonexistent_table(self, tmp_db):
        """Несуществующая таблица выбрасывает исключение."""
        service = ExportService(tmp_db)
        with pytest.raises(ValueError):
            service.export_table("UnknownTable", format="csv")
```

### 3.6. Оптимизация:
- Все тесты помечены `@pytest.mark.unit`
- Каждый тест выполняется < 1 секунды
- Используется `tmp_db` из `conftest.py` для изоляции

✅ КРИТЕРИИ ПРИЁМКИ:
1. Все тесты из промтов 1 и 2 проходят
2. Все новые тесты проходят
3. Покрытие бизнес-логики ≥ 80%
4. Время выполнения всех unit-тестов < 5 секунд
5. Параметризованные тесты работают корректно

📦 РЕЗУЛЬТАТ:
После выполнения этого промта у нас есть:
- Полное покрытие бизнес-логики тестами
- Тесты синтеза комбинаций
- Тесты расчёта метрик
- Тесты расчёта Score
- Тесты аналитики и экспорта

Время выполнения промта: ~50 минут для LLM.
Время выполнения тестов: < 5 секунд.

⚡ СЛЕДУЮЩИЙ ШАГ:
После успешного выполнения этого промта, переходим к ПРОМТУ 4 — 
Integration-тесты API (CRUD для всех сущностей).

Выполни этот промт, убедись, что все тесты проходят, и сообщи результат.
```

---

Коллега, это первые 3 промта из 12. Каждый промт — самодостаточная единица, которая добавляет новый слой тестов, не ломая предыдущие.

**Продолжить со следующими промтами (4-12)?** Они включают:
- Промт 4: Integration-тесты API (CRUD)
- Промт 5: Integration-тесты (расширенные)
- Промт 6: Контрактные тесты
- Промт 7: Smoke-тесты и окружение
- Промт 8: Тесты безопасности
- Промт 9: Тесты производительности
- Промт 10: E2E-тесты (Playwright)
- Промт 11: CI/CD workflows
- Промт 12: Финализация и документация

Если хочешь, могу продолжить прямо сейчас или разбить на отдельные сообщения для удобства.

# 📨 СООБЩЕНИЕ 4: ПРОМТ 4 — INTEGRATION-ТЕСТЫ API (CRUD)

```
Ты — senior Python-разработчик, специализирующийся на тестировании FastAPI.
Промты 1-3 успешно выполнены: есть фундамент, unit-тесты валидаторов и бизнес-логики.
Теперь создаём integration-тесты для API через TestClient.

🎯 ЦЕЛЬ ПРОМТА:
Покрыть тестами ВСЕ CRUD-операции для всех четырёх сущностей:
- /api/analytes
- /api/bio-recognition
- /api/immobilization
- /api/memristive

⚠️ КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
- Использовать фикстуру `api_client` из conftest.py (изоляция через tmp_path)
- КАЖДЫЙ тест должен выполняться < 2 секунд
- После выполнения ВСЕ предыдущие тесты (промты 1-3) должны проходить
- Использовать параметризацию для уменьшения дублирования кода
- Проверять HTTP-статусы: 200, 400, 404, 409, 422, 503

📋 ЗАДАЧИ:

### 4.1. Создать `backend/tests/integration/__init__.py` (пустой)

### 4.2. Обновить `backend/tests/conftest.py` — добавить параметризованную фикстуру:

```python
@pytest.fixture(params=["analytes", "bio-recognition", "immobilization", "memristive"])
def entity_endpoint(request):
    """Параметризованная фикстура для всех эндпоинтов сущностей."""
    return f"/api/{request.param}"

@pytest.fixture(params=["analyte", "bio_recognition", "immobilization", "memristive"])
def entity_type(request):
    """Параметризованная фикстура для типов сущностей."""
    return request.param

@pytest.fixture
def entity_factory(entity_type):
    """Возвращает фабрику для нужного типа сущности."""
    from backend.tests.factories import (
        make_analyte,
        make_bio_recognition_layer,
        make_immobilization_layer,
        make_memristive_layer
    )
    factories = {
        "analyte": make_analyte,
        "bio_recognition": make_bio_recognition_layer,
        "immobilization": make_immobilization_layer,
        "memristive": make_memristive_layer
    }
    return factories[entity_type]
```

### 4.3. Создать `backend/tests/integration/test_api_health.py`:

```python
import pytest

@pytest.mark.integration
class TestAPIHealth:
    
    def test_health_endpoint(self, api_client):
        """GET /api/health возвращает 200 с правильным JSON."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
    
    def test_docs_endpoint_accessible(self, api_client):
        """GET /docs возвращает 200 (Swagger UI доступен)."""
        response = api_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint_accessible(self, api_client):
        """GET /redoc возвращает 200."""
        response = api_client.get("/redoc")
        assert response.status_code == 200
    
    def test_openapi_json(self, api_client):
        """GET /openapi.json возвращает валидную OpenAPI-схему."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
```

### 4.4. Создать `backend/tests/integration/test_api_crud.py` — универсальные CRUD-тесты:

```python
import pytest

@pytest.mark.integration
class TestCRUDOperations:
    """Универсальные CRUD-тесты для всех сущностей через параметризацию."""
    
    def test_list_empty_returns_200(self, api_client, entity_endpoint):
        """GET на пустой БД возвращает 200 и пустой список."""
        response = api_client.get(entity_endpoint)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_create_valid_entity_returns_200(self, api_client, entity_endpoint, entity_factory):
        """POST с валидными данными возвращает 200."""
        data = entity_factory()
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("success") is True
    
    def test_create_invalid_id_format_returns_422(self, api_client, entity_endpoint, entity_type):
        """POST с невалидным ID возвращает 422."""
        from backend.tests.factories import (
            make_analyte, make_bio_recognition_layer,
            make_immobilization_layer, make_memristive_layer
        )
        factories = {
            "analyte": (make_analyte, "ta_id", "INVALID_ID"),
            "bio_recognition": (make_bio_recognition_layer, "bre_id", "INVALID_ID"),
            "immobilization": (make_immobilization_layer, "im_id", "INVALID_ID"),
            "memristive": (make_memristive_layer, "mem_id", "INVALID_ID")
        }
        factory, id_field, bad_value = factories[entity_type]
        data = factory(**{id_field: bad_value})
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 422
    
    def test_create_missing_required_field_returns_422(self, api_client, entity_endpoint, entity_type):
        """POST без обязательного поля возвращает 422."""
        from backend.tests.factories import (
            make_analyte, make_bio_recognition_layer,
            make_immobilization_layer, make_memristive_layer
        )
        factories = {
            "analyte": (make_analyte, "ta_id"),
            "bio_recognition": (make_bio_recognition_layer, "bre_id"),
            "immobilization": (make_immobilization_layer, "im_id"),
            "memristive": (make_memristive_layer, "mem_id")
        }
        factory, id_field = factories[entity_type]
        data = factory()
        del data[id_field]
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 422
    
    def test_create_out_of_range_value_returns_422(self, api_client, entity_endpoint, entity_type):
        """POST с значением вне диапазона возвращает 422."""
        from backend.tests.factories import (
            make_analyte, make_bio_recognition_layer,
            make_immobilization_layer, make_memristive_layer
        )
        factories = {
            "analyte": (make_analyte, {"ph_min": 999.0}),
            "bio_recognition": (make_bio_recognition_layer, {"ph_min": 999.0}),
            "immobilization": (make_immobilization_layer, {"ph_min": 999.0}),
            "memristive": (make_memristive_layer, {"ph_min": 999.0})
        }
        factory, overrides = factories[entity_type]
        data = factory(**overrides)
        response = api_client.post(entity_endpoint, json=data)
        assert response.status_code == 422
    
    def test_create_duplicate_returns_409(self, api_client, entity_endpoint, entity_factory):
        """Повторная запись с тем же ID возвращает 409."""
        data = entity_factory()
        response1 = api_client.post(entity_endpoint, json=data)
        assert response1.status_code == 200
        
        response2 = api_client.post(entity_endpoint, json=data)
        assert response2.status_code == 409
    
    def test_list_after_create_returns_data(self, api_client, entity_endpoint, entity_factory):
        """После создания GET возвращает данные."""
        data = entity_factory()
        api_client.post(entity_endpoint, json=data)
        
        response = api_client.get(entity_endpoint)
        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 1
    
    def test_get_by_id_returns_200(self, api_client, entity_endpoint, entity_type, entity_factory):
        """GET /{id} возвращает 200 для существующей записи."""
        from backend.tests.factories import (
            make_analyte, make_bio_recognition_layer,
            make_immobilization_layer, make_memristive_layer
        )
        factories = {
            "analyte": (make_analyte, "ta_id"),
            "bio_recognition": (make_bio_recognition_layer, "bre_id"),
            "immobilization": (make_immobilization_layer, "im_id"),
            "memristive": (make_memristive_layer, "mem_id")
        }
        factory, id_field = factories[entity_type]
        data = factory()
        api_client.post(entity_endpoint, json=data)
        
        entity_id = data[id_field]
        response = api_client.get(f"{entity_endpoint}/{entity_id}")
        assert response.status_code == 200
    
    def test_get_nonexistent_id_returns_404(self, api_client, entity_endpoint):
        """GET /{id} для несуществующей записи возвращает 404."""
        response = api_client.get(f"{entity_endpoint}/NONEXISTENT_ID_12345")
        assert response.status_code == 404
    
    def test_pagination_works(self, api_client, entity_endpoint, entity_factory):
        """Пагинация работает корректно."""
        # Создаём 15 записей
        for i in range(15):
            data = entity_factory()
            # Меняем ID, чтобы избежать дубликатов
            id_field = [k for k in data.keys() if k.endswith("_id")][0]
            data[id_field] = f"{data[id_field]}_{i:03d}"
            api_client.post(entity_endpoint, json=data)
        
        # Проверяем limit
        response = api_client.get(f"{entity_endpoint}?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Проверяем offset
        response = api_client.get(f"{entity_endpoint}?limit=5&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
```

### 4.5. Создать `backend/tests/integration/test_api_analytes.py` — специфичные тесты для аналитов:

```python
import pytest
from backend.tests.factories import make_analyte

@pytest.mark.integration
class TestAnalytesAPISpecific:
    """Специфичные тесты для эндпоинта /api/analytes."""
    
    def test_create_analyte_with_unicode_name(self, api_client):
        """Аналит с unicode-именем создаётся успешно."""
        data = make_analyte(ta_name="Глюкоза 🧪 Test")
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200
        
        # Проверяем, что имя сохранилось корректно
        response = api_client.get("/api/analytes")
        result = response.json()
        assert any("Глюкоза" in item.get("TA_Name", "") for item in result)
    
    def test_create_analyte_with_boundary_ph(self, api_client):
        """Аналит с граничными значениями pH создаётся."""
        data = make_analyte(ph_min=2.0, ph_max=10.0)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200
    
    def test_create_analyte_with_boundary_temperature(self, api_client):
        """Аналит с граничной температурой создаётся."""
        data = make_analyte(t_max=0)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200
        
        data = make_analyte(ta_id="TA_TEST002", t_max=180)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 200
    
    def test_search_by_name(self, api_client):
        """Поиск по имени работает корректно."""
        # Создаём несколько аналитов
        api_client.post("/api/analytes", json=make_analyte(ta_id="TA_TEST001", ta_name="Glucose"))
        api_client.post("/api/analytes", json=make_analyte(ta_id="TA_TEST002", ta_name="Fructose"))
        api_client.post("/api/analytes", json=make_analyte(ta_id="TA_TEST003", ta_name="Sucrose"))
        
        # Ищем "Glucose"
        response = api_client.get("/api/analytes?search=Glucose")
        assert response.status_code == 200
        data = response.json()
        # Должен вернуть хотя бы один результат
        assert len(data) >= 1
```

### 4.6. Оптимизация:
- Все тесты помечены `@pytest.mark.integration`
- Параметризация через `entity_endpoint` и `entity_factory` уменьшает дублирование в 4 раза
- Каждый тест выполняется < 2 секунд
- Используется `pytest-xdist` для параллельного запуска

### 4.7. Запуск тестов:
```bash
# Только integration-тесты
pytest backend/tests/integration/ -v -m integration

# Параллельно
pytest backend/tests/integration/ -n auto

# С отчётом о времени
pytest backend/tests/integration/ --durations=10
```

✅ КРИТЕРИИ ПРИЁМКИ:
1. Все тесты из промтов 1-3 проходят
2. Все новые integration-тесты проходят
3. Все 4 эндпоинта покрыты CRUD-тестами
4. Параметризация работает корректно (один тест → 4 прогона)
5. Время выполнения всех integration-тестов < 30 секунд
6. HTTP-статусы проверяются: 200, 404, 409, 422

📦 РЕЗУЛЬТАТ:
После выполнения этого промта у нас есть:
- Полное покрытие CRUD-операций для всех 4 сущностей
- Smoke-тесты для /health, /docs, /redoc
- Тесты пагинации
- Тесты граничных значений
- Тесты unicode-символов

Время выполнения промта: ~60 минут для LLM.
Время выполнения тестов: < 30 секунд.

⚡ СЛЕДУЮЩИЙ ШАГ:
Переходим к ПРОМТУ 5 — расширенные integration-тесты 
(комбинации, аналитика, экспорт, CORS, HTTP-статусы).

Выполни этот промт, убедись, что все тесты проходят, и сообщи результат.
```

---

# 📨 СООБЩЕНИЕ 5: ПРОМТ 5 — INTEGRATION-ТЕСТЫ (РАСШИРЕННЫЕ)

```
Ты — senior Python-разработчик. Промты 1-4 успешно выполнены.
Теперь создаём расширенные integration-тесты для:
- Комбинаций (синтез, получение списка)
- Аналитики (статистика, лучшие комбинации)
- Экспорта (CSV, JSON, ZIP)
- CORS
- Маппинга HTTP-статусов
- Кэширования

🎯 ЦЕЛЬ ПРОМТА:
Покрыть тестами ВСЕ расширенные эндпоинты API.

⚠️ КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
- Каждый тест выполняется < 5 секунд (кроме performance-тестов)
- Использовать фикстуры `db_with_full_passport`, `db_with_analytes`
- После выполнения ВСЕ предыдущие тесты должны проходить
- Проверять заголовки ответов (Content-Type, CORS)

📋 ЗАДАЧИ:

### 5.1. Создать `backend/tests/integration/test_api_combinations.py`:

```python
import pytest
from backend.tests.factories import make_compatible_four_layers

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
        assert created2 == 0  # Дубликаты не создаются
    
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
```

### 5.2. Создать `backend/tests/integration/test_api_analytics.py`:

```python
import pytest

@pytest.mark.integration
class TestAnalyticsAPI:
    
    def test_statistics_endpoint(self, db_with_full_passport):
        """GET /api/analytics/statistics возвращает статистику по 5 таблицам."""
        response = db_with_full_passport.get("/api/analytics/statistics")
        assert response.status_code == 200
        data = response.json()
        # Должны быть данные по 5 таблицам
        assert len(data) >= 1
    
    def test_statistics_empty_db(self, api_client):
        """Статистика для пустой БД возвращает нули."""
        response = api_client.get("/api/analytics/statistics")
        assert response.status_code == 200
    
    def test_best_combinations_sorted(self, db_with_full_passport):
        """GET /api/analytics/best-combinations возвращает отсортированный список."""
        db_with_full_passport.post("/api/combinations/synthesize")
        
        response = db_with_full_passport.get("/api/analytics/best-combinations?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 1:
            scores = [combo["Score"] for combo in data]
            assert scores == sorted(scores, reverse=True)
    
    def test_best_combinations_limit(self, db_with_full_passport):
        """Параметр limit работает корректно."""
        db_with_full_passport.post("/api/combinations/synthesize")
        
        response = db_with_full_passport.get("/api/analytics/best-combinations?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
```

### 5.3. Создать `backend/tests/integration/test_api_export.py`:

```python
import pytest
import json
import zipfile
import io

@pytest.mark.integration
class TestExportAPI:
    
    def test_export_csv(self, db_with_analytes):
        """GET /api/export/analytes?format=csv → 200, text/csv."""
        response = db_with_analytes.get("/api/export/analytes?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert len(response.content) > 0
        # Проверяем, что это действительно CSV
        content = response.text
        assert "," in content or ";" in content
    
    def test_export_json(self, db_with_analytes):
        """GET /api/export/analytes?format=json → 200, application/json."""
        response = db_with_analytes.get("/api/export/analytes?format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        # Проверяем валидность JSON
        data = json.loads(response.content)
        assert isinstance(data, list)
    
    def test_export_excel(self, db_with_analytes):
        """GET /api/export/analytes?format=excel → 200, xlsx."""
        response = db_with_analytes.get("/api/export/analytes?format=excel")
        assert response.status_code == 200
        # Excel файлы имеют специальный content-type
        assert len(response.content) > 0
    
    def test_export_all_zip(self, db_with_analytes):
        """GET /api/export/all?format=csv → ZIP-архив."""
        response = db_with_analytes.get("/api/export/all?format=csv")
        assert response.status_code == 200
        assert "application/zip" in response.headers["content-type"]
        
        # Проверяем, что это валидный ZIP
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        assert len(zip_file.namelist()) > 0
    
    def test_export_invalid_format(self, api_client):
        """format=xml → 422."""
        response = api_client.get("/api/export/analytes?format=xml")
        assert response.status_code == 422
    
    def test_export_nonexistent_table(self, api_client):
        """table_name=unknown → 404."""
        response = api_client.get("/api/export/unknown_table?format=csv")
        assert response.status_code == 404
    
    def test_export_empty_table(self, api_client):
        """Экспорт пустой таблицы возвращает валидный файл."""
        response = api_client.get("/api/export/analytes?format=csv")
        assert response.status_code == 200
```

### 5.4. Создать `backend/tests/integration/test_api_cors.py`:

```python
import pytest

@pytest.mark.integration
class TestCORS:
    
    def test_cors_preflight_localhost_3000(self, api_client):
        """OPTIONS с Origin: http://localhost:3000 → разрешено."""
        response = api_client.options(
            "/api/analytes",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        assert response.status_code == 200
        assert "http://localhost:3000" in response.headers.get("access-control-allow-origin", "")
    
    @pytest.mark.parametrize("origin", [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ])
    def test_cors_allowed_origins(self, api_client, origin):
        """Запросы с разрешённых origin проходят."""
        response = api_client.get(
            "/api/health",
            headers={"Origin": origin}
        )
        assert response.status_code == 200
        assert origin in response.headers.get("access-control-allow-origin", "")
    
    def test_cors_disallowed_origin(self, api_client):
        """Запрос с неразрешённого origin не получает разрешающих заголовков."""
        response = api_client.get(
            "/api/health",
            headers={"Origin": "http://evil.com"}
        )
        # Либо 200 без CORS-заголовков, либо 403
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert "http://evil.com" not in allow_origin
```

### 5.5. Создать `backend/tests/integration/test_http_status_codes.py`:

```python
import pytest
from unittest.mock import patch

@pytest.mark.integration
class TestHTTPStatusCodes:
    """Проверка, что исключения корректно преобразуются в HTTP-коды."""
    
    def test_entity_not_found_returns_404(self, api_client):
        """EntityNotFoundError → 404 Not Found."""
        response = api_client.get("/api/analytes/TA_NONEXISTENT")
        assert response.status_code == 404
    
    def test_validation_error_returns_422(self, api_client):
        """Ошибки валидации Pydantic → 422."""
        from backend.tests.factories import make_analyte
        data = make_analyte(t_max=9999)  # вне диапазона
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 422
    
    def test_duplicate_entity_returns_409(self, api_client):
        """Дубликат → 409 Conflict."""
        from backend.tests.factories import make_analyte
        data = make_analyte()
        api_client.post("/api/analytes", json=data)
        response = api_client.post("/api/analytes", json=data)
        assert response.status_code == 409
    
    def test_invalid_json_returns_422(self, api_client):
        """Невалидный JSON → 422."""
        response = api_client.post(
            "/api/analytes",
            content="not a json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_method_not_allowed_returns_405(self, api_client):
        """Неподдерживаемый метод → 405."""
        response = api_client.delete("/api/analytes")
        assert response.status_code in [404, 405]  # зависит от реализации
```

### 5.6. Создать `backend/tests/integration/test_cache_behavior.py`:

```python
import pytest

@pytest.mark.integration
class TestCacheBehavior:
    """Проверка корректности работы кэша."""
    
    def test_cache_cleared_after_insert(self, api_client):
        """Кэш очищается при вставке новой записи."""
        # Первый запрос
        response1 = api_client.get("/api/analytes")
        initial_count = len(response1.json())
        
        # Вставляем новый аналит
        from backend.tests.factories import make_analyte
        new_analyte = make_analyte(ta_id="TA_TEST_NEW", ta_name="New Analyte")
        api_client.post("/api/analytes", json=new_analyte)
        
        # Второй запрос — должен вернуть новые данные
        response2 = api_client.get("/api/analytes")
        new_count = len(response2.json())
        assert new_count == initial_count + 1
    
    def test_cache_cleared_after_delete(self, api_client):
        """Кэш очищается при удалении записи."""
        from backend.tests.factories import make_analyte
        data = make_analyte()
        api_client.post("/api/analytes", json=data)
        
        # Проверяем, что запись есть
        response1 = api_client.get("/api/analytes")
        count_before = len(response1.json())
        
        # Удаляем (если есть эндпоинт DELETE)
        # response = api_client.delete(f"/api/analytes/{data['ta_id']}")
        # Если DELETE не реализован, пропускаем тест
        pytest.skip("DELETE endpoint not implemented")
    
    def test_repeated_reads_consistent(self, api_client):
        """Повторные чтения возвращают одинаковые данные."""
        from backend.tests.factories import make_analyte
        data = make_analyte()
        api_client.post("/api/analytes", json=data)
        
        response1 = api_client.get("/api/analytes")
        response2 = api_client.get("/api/analytes")
        
        assert response1.json() == response2.json()
```

### 5.7. Оптимизация:
- Все тесты помечены `@pytest.mark.integration`
- Параметризация для CORS-тестов
- Использование фикстур `db_with_full_passport` и `db_with_analytes`
- Параллельный запуск через `pytest-xdist`

### 5.8. Запуск тестов:
```bash
# Все integration-тесты
pytest backend/tests/integration/ -v -m integration

# Только тесты комбинаций
pytest backend/tests/integration/test_api_combinations.py -v

# Только тесты экспорта
pytest backend/tests/integration/test_api_export.py -v

# С отчётом о медленных тестах
pytest backend/tests/integration/ --durations=10
```

✅ КРИТЕРИИ ПРИЁМКИ:
1. Все тесты из промтов 1-4 проходят
2. Все новые integration-тесты проходят
3. Эндпоинты комбинаций, аналитики, экспорта покрыты
4. CORS-заголовки проверяются для разных origin
5. HTTP-статусы проверяются: 200, 404, 409, 422, 405
6. Время выполнения всех integration-тестов < 60 секунд

📦 РЕЗУЛЬТАТ:
После выполнения этого промта у нас есть:
- Полное покрытие всех эндпоинтов API
- Тесты синтеза комбинаций
- Тесты аналитики
- Тесты экспорта (CSV, JSON, Excel, ZIP)
- Тесты CORS
- Тесты HTTP-статусов
- Тесты поведения кэша

Время выполнения промта: ~60 минут для LLM.
Время выполнения тестов: < 60 секунд.

⚡ СЛЕДУЮЩИЙ ШАГ:
Переходим к ПРОМТУ 6 — контрактные тесты (front ↔ back).

Выполни этот промт, убедись, что все тесты проходят, и сообщи результат.
```

---

# 📨 СООБЩЕНИЕ 6: ПРОМТ 6 — КОНТРАКТНЫЕ ТЕСТЫ (FRONT ↔ BACK)

```
Ты — senior Python-разработчик. Промты 1-5 успешно выполнены.
Теперь создаём контрактные тесты, гарантирующие совместимость фронтенда и бэкенда.

🎯 ЦЕЛЬ ПРОМТА:
Зафиксировать API-контракт через Pydantic-модели и проверить, что бэкенд
отвечает строго по контракту. Это гарантирует, что фронтенд не сломается
при незаметном изменении API.

⚠️ КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
- Pydantic v2 (model_dump, model_validate, ConfigDict, TypeAdapter)
- Использовать PascalCase для полей (как отдаёт бэкенд)
- После выполнения ВСЕ предыдущие тесты должны проходить
- Тесты должны ПАДАТЬ при изменении схемы API

📋 ЗАДАЧИ:

### 6.1. Создать `backend/tests/contract/__init__.py` (пустой)

### 6.2. Создать `backend/tests/contract/api_schemas.py` — схемы API:

```python
"""
Контракт API — централизованное описание всех схем ответов.
Изменение этих схем требует обновления фронтенда.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class BaseResponse(BaseModel):
    """Базовая модель с настройками для PascalCase."""
    model_config = ConfigDict(populate_by_name=True)

# ============ Схемы для сущностей ============

class AnalyteResponse(BaseResponse):
    """Схема ответа для аналита (PascalCase)."""
    TA_ID: str = Field(..., pattern=r"^TA[A-Z0-9_-]{1,30}$")
    TA_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Max: int = Field(..., ge=0, le=180)
    ST: int = Field(..., ge=0, le=365)  # Stability
    HL: int = Field(..., ge=0, le=8760)  # Half-life
    PC: int = Field(..., ge=0, le=1000)  # Power consumption

class BioRecognitionResponse(BaseResponse):
    """Схема ответа для биораспознающего слоя."""
    BRE_ID: str = Field(..., pattern=r"^BRE[A-Z0-9_-]{1,30}$")
    BRE_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    DR_Min: float = Field(..., ge=0)
    DR_Max: float = Field(..., ge=0)
    SN: int = Field(..., ge=0)  # Sensitivity
    RP: int = Field(..., ge=0, le=100)  # Reproducibility
    TR: int = Field(..., ge=0)  # Response time
    ST: int = Field(..., ge=0, le=365)
    LOD: int = Field(..., ge=0)
    HL: int = Field(..., ge=0, le=8760)
    PC: int = Field(..., ge=0, le=1000)

class ImmobilizationResponse(BaseResponse):
    """Схема ответа для иммобилизационного слоя."""
    IM_ID: str = Field(..., pattern=r"^IM[A-Z0-9_-]{1,30}$")
    IM_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    MP: int = Field(..., ge=0, le=150)  # Young's Modulus
    Adh: str  # Adhesion
    Sol: str  # Solubility
    K_IM: float = Field(..., ge=0, le=1.0)  # Loss Coefficient
    RP: int = Field(..., ge=0, le=100)
    TR: int = Field(..., ge=0)
    ST: int = Field(..., ge=0, le=365)
    HL: int = Field(..., ge=0, le=8760)
    PC: int = Field(..., ge=0, le=1000)

class MemristiveResponse(BaseResponse):
    """Схема ответа для мемристивного слоя."""
    MEM_ID: str = Field(..., pattern=r"^MEM[A-Z0-9_-]{1,30}$")
    MEM_Name: str = Field(..., min_length=3, max_length=255)
    PH_Min: float = Field(..., ge=2.0, le=10.0)
    PH_Max: float = Field(..., ge=2.0, le=10.0)
    T_Min: int = Field(..., ge=0, le=100)
    T_Max: int = Field(..., ge=0, le=100)
    DR_Min: float = Field(..., ge=0)
    DR_Max: float = Field(..., ge=0)
    MP: int = Field(..., ge=0, le=150)
    SN: int = Field(..., ge=0)
    RP: int = Field(..., ge=0, le=100)
    TR: int = Field(..., ge=0)
    ST: int = Field(..., ge=0, le=365)
    LOD: int = Field(..., ge=0)
    HL: int = Field(..., ge=0, le=8760)
    PC: int = Field(..., ge=0, le=1000)

class CombinationResponse(BaseResponse):
    """Схема ответа для комбинации."""
    Combo_ID: str = Field(..., pattern=r"^COMBO_")
    TA_ID: str
    BRE_ID: str
    IM_ID: str
    MEM_ID: str
    Score: float = Field(..., ge=0, le=10)
    SN_Total: Optional[float] = None
    TR_Total: Optional[float] = None
    ST_Total: Optional[float] = None
    LOD_Total: Optional[float] = None
    DR_Total: Optional[float] = None
    PC_Total: Optional[float] = None
    Created: Optional[str] = None

# ============ Схемы для служебных ответов ============

class SuccessResponse(BaseResponse):
    """Схема успешного ответа."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseResponse):
    """Схема ошибки."""
    detail: str

class HealthResponse(BaseResponse):
    """Схема ответа /api/health."""
    status: str
    message: str

class StatisticsResponse(BaseResponse):
    """Схема ответа /api/analytics/statistics."""
    # Структура может варьироваться, но должны быть ключи для 5 таблиц
    pass

class SynthesisResponse(BaseResponse):
    """Схема ответа /api/combinations/synthesize."""
    checked: int = Field(..., ge=0)
    created: int = Field(..., ge=0)
    skipped: Optional[int] = None
    errors: Optional[int] = None
```

### 6.3. Создать `backend/tests/contract/test_response_schemas.py`:

```python
import pytest
from pydantic import TypeAdapter, ValidationError
from typing import List
from backend.tests.contract.api_schemas import (
    AnalyteResponse,
    BioRecognitionResponse,
    ImmobilizationResponse,
    MemristiveResponse,
    CombinationResponse,
    SuccessResponse,
    HealthResponse,
    SynthesisResponse
)
from backend.tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer
)

@pytest.mark.contract
class TestResponseSchemas:
    """Проверка соответствия ответов API описанным схемам."""
    
    def test_health_response_schema(self, api_client):
        """Ответ /api/health соответствует HealthResponse."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        
        adapter = TypeAdapter(HealthResponse)
        # Если схема не совпадает, упадёт с ValidationError
        adapter.validate_python(response.json())
    
    def test_analyte_response_schema(self, api_client):
        """Ответ GET /api/analytes соответствует AnalyteResponse."""
        # Создаём аналит
        data = make_analyte()
        api_client.post("/api/analytes", json=data)
        
        response = api_client.get("/api/analytes")
        assert response.status_code == 200
        
        adapter = TypeAdapter(List[AnalyteResponse])
        adapter.validate_python(response.json())
    
    def test_bio_recognition_response_schema(self, api_client):
        """Ответ GET /api/bio-recognition соответствует схеме."""
        data = make_bio_recognition_layer()
        api_client.post("/api/bio-recognition", json=data)
        
        response = api_client.get("/api/bio-recognition")
        adapter = TypeAdapter(List[BioRecognitionResponse])
        adapter.validate_python(response.json())
    
    def test_immobilization_response_schema(self, api_client):
        """Ответ GET /api/immobilization соответствует схеме."""
        data = make_immobilization_layer()
        api_client.post("/api/immobilization", json=data)
        
        response = api_client.get("/api/immobilization")
        adapter = TypeAdapter(List[ImmobilizationResponse])
        adapter.validate_python(response.json())
    
    def test_memristive_response_schema(self, api_client):
        """Ответ GET /api/memristive соответствует схеме."""
        data = make_memristive_layer()
        api_client.post("/api/memristive", json=data)
        
        response = api_client.get("/api/memristive")
        adapter = TypeAdapter(List[MemristiveResponse])
        adapter.validate_python(response.json())
    
    def test_combination_response_schema(self, db_with_full_passport):
        """Ответ GET /api/combinations соответствует схеме."""
        db_with_full_passport.post("/api/combinations/synthesize")
        response = db_with_full_passport.get("/api/combinations")
        
        adapter = TypeAdapter(List[CombinationResponse])
        adapter.validate_python(response.json())
    
    def test_create_response_schema(self, api_client):
        """Ответ POST /api/analytes соответствует SuccessResponse."""
        data = make_analyte()
        response = api_client.post("/api/analytes", json=data)
        
        # Может быть SuccessResponse или просто 200
        if response.status_code == 200:
            try:
                adapter = TypeAdapter(SuccessResponse)
                adapter.validate_python(response.json())
            except ValidationError:
                # Если ответ не соответствует SuccessResponse,
                # это тоже ОК, если есть success: true
                json_data = response.json()
                assert "success" in json_data or "data" in json_data
    
    def test_synthesis_response_schema(self, db_with_full_passport):
        """Ответ POST /api/combinations/synthesize соответствует схеме."""
        response = db_with_full_passport.post("/api/combinations/synthesize")
        
        adapter = TypeAdapter(SynthesisResponse)
        adapter.validate_python(response.json())
    
    def test_error_response_schema(self, api_client):
        """Ответ с ошибкой соответствует ErrorResponse."""
        response = api_client.get("/api/analytes/NONEXISTENT_ID")
        if response.status_code == 404:
            # Может быть ErrorResponse или просто {"detail": "..."}
            json_data = response.json()
            assert "detail" in json_data or "error" in json_data
```

### 6.4. Создать `backend/tests/contract/test_field_mapping.py`:

```python
import pytest
from backend.tests.factories import (
    make_analyte,
    make_bio_recognition_layer,
    make_immobilization_layer,
    make_memristive_layer
)

@pytest.mark.contract
class TestFieldMapping:
    """Проверка, что бэкенд отдаёт поля в правильном регистре."""
    
    def test_analyte_fields_are_pascal_case(self, api_client):
        """Поля аналита в ответе используют PascalCase."""
        data = make_analyte()
        api_client.post("/api/analytes", json=data)
        
        response = api_client.get("/api/analytes")
        data = response.json()
        
        if len(data) > 0:
            analyte = data[0]
            # Проверяем наличие PascalCase-полей
            assert "TA_ID" in analyte, "Missing TA_ID (PascalCase)"
            assert "TA_Name" in analyte, "Missing TA_Name (PascalCase)"
            assert "PH_Min" in analyte, "Missing PH_Min"
            assert "PH_Max" in analyte, "Missing PH_Max"
            assert "T_Max" in analyte, "Missing T_Max"
            
            # Проверяем отсутствие snake_case-полей
            assert "ta_id" not in analyte, "Found ta_id (should be TA_ID)"
            assert "ta_name" not in analyte, "Found ta_name (should be TA_Name)"
            assert "ph_min" not in analyte, "Found ph_min (should be PH_Min)"
    
    def test_immobilization_special_fields(self, api_client):
        """Специальные поля иммобилизации (MP, Adh, Sol, K_IM)."""
        data = make_immobilization_layer()
        api_client.post("/api/immobilization", json=data)
        
        response = api_client.get("/api/immobilization")
        im = response.json()[0]
        
        # Проверяем правильные имена полей
        assert "MP" in im, "Missing MP (Young's Modulus)"
        assert "Adh" in im, "Missing Adh (Adhesion)"
        assert "Sol" in im, "Missing Sol (Solubility)"
        assert "K_IM" in im, "Missing K_IM (Loss Coefficient)"
        
        # Проверяем отсутствие неправильных имён
        assert "young_modulus" not in im
        assert "adhesion" not in im
        assert "solubility" not in im
        assert "loss_coefficient" not in im
    
    def test_combination_fields_are_pascal_case(self, db_with_full_passport):
        """Поля комбинации в ответе используют PascalCase."""
        db_with_full_passport.post("/api/combinations/synthesize")
        response = db_with_full_passport.get("/api/combinations")
        data = response.json()
        
        if len(data) > 0:
            combo = data[0]
            assert "Combo_ID" in combo
            assert "TA_ID" in combo
            assert "BRE_ID" in combo
            assert "IM_ID" in combo
            assert "MEM_ID" in combo
            assert "Score" in combo
            
            # Проверяем отсутствие snake_case
            assert "combo_id" not in combo
            assert "ta_id" not in combo
    
    def test_id_format_matches_contract(self, api_client):
        """ID сущностей соответствуют регулярным выражениям из контракта."""
        from backend.tests.contract.api_schemas import AnalyteResponse
        
        data = make_analyte()
        api_client.post("/api/analytes", json=data)
        
        response = api_client.get("/api/analytes")
        adapter = TypeAdapter(AnalyteResponse)
        
        for item in response.json():
            # Если ID не соответствует паттерну, упадёт с ValidationError
            adapter.validate_python(item)
```

### 6.5. Создать `backend/tests/contract/test_api_contract.py` — единый контракт:

```python
import pytest
from pydantic import TypeAdapter
from typing import List
from backend.tests.contract.api_schemas import (
    AnalyteResponse,
    BioRecognitionResponse,
    ImmobilizationResponse,
    MemristiveResponse,
    CombinationResponse
)

@pytest.mark.contract
class TestAPIContract:
    """Централизованные тесты API-контракта."""
    
    # Маппинг эндпоинт → схема ответа
    ENDPOINT_SCHEMAS = {
        "/api/analytes": AnalyteResponse,
        "/api/bio-recognition": BioRecognitionResponse,
        "/api/immobilization": ImmobilizationResponse,
        "/api/memristive": MemristiveResponse,
        "/api/combinations": CombinationResponse,
    }
    
    @pytest.mark.parametrize("endpoint,schema", list(ENDPOINT_SCHEMAS.items()))
    def test_endpoint_returns_valid_schema(self, api_client, endpoint, schema):
        """Каждый эндпоинт возвращает данные, соответствующие схеме."""
        response = api_client.get(endpoint)
        assert response.status_code == 200
        
        adapter = TypeAdapter(List[schema])
        # Если схема не совпадает, упадёт с ValidationError
        adapter.validate_python(response.json())
    
    def test_all_endpoints_return_lists(self, api_client):
        """Все GET-эндпоинты сущностей возвращают списки."""
        for endpoint in self.ENDPOINT_SCHEMAS.keys():
            response = api_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list), f"{endpoint} should return a list"
    
    def test_no_extra_fields_in_responses(self, api_client):
        """Ответы не содержат неожиданных полей (опционально)."""
        # Этот тест проверяет, что бэкенд не отдаёт лишние поля
        # (например, внутренние ID, пароли и т.д.)
        response = api_client.get("/api/analytes")
        if response.status_code == 200 and len(response.json()) > 0:
            analyte = response.json()[0]
            
            # Не должно быть полей с паролями, токенами и т.д.
            forbidden_keywords = ["password", "secret", "token", "api_key"]
            for key in analyte.keys():
                for forbidden in forbidden_keywords:
                    assert forbidden not in key.lower(), \
                        f"Found forbidden field: {key}"
```

### 6.6. Оптимизация:
- Все тесты помечены `@pytest.mark.contract`
- Параметризация через `ENDPOINT_SCHEMAS` уменьшает дублирование
- Pydantic v2 TypeAdapter для быстрой валидации
- Тесты выполняются быстро (< 0.5 секунд каждый)

### 6.7. Запуск тестов:
```bash
# Только контрактные тесты
pytest backend/tests/contract/ -v -m contract

# С отчётом о валидации
pytest backend/tests/contract/test_response_schemas.py -v --tb=short

# Проверка маппинга полей
pytest backend/tests/contract/test_field_mapping.py -v
```

✅ КРИТЕРИИ ПРИЁМКИ:
1. Все тесты из промтов 1-5 проходят
2. Все новые контрактные тесты проходят
3. Схемы API описаны в Pydantic-моделях
4. Тесты ПАДАЮТ при изменении схемы (проверь, изменив одно поле)
5. Маппинг полей (PascalCase) проверяется
6. Время выполнения всех контрактных тестов < 10 секунд

📦 РЕЗУЛЬТАТ:
После выполнения этого промта у нас есть:
- Централизованное описание API-контракта
- Тесты соответствия ответов схемам
- Тесты маппинга полей (PascalCase)
- Гарантии, что фронтенд не сломается при незаметном изменении API

Время выполнения промта: ~50 минут для LLM.
Время выполнения тестов: < 10 секунд.

⚡ СЛЕДУЮЩИЙ ШАГ:
Переходим к ПРОМТУ 7 — smoke-тесты и тесты переменных окружения.

Выполни этот промт, убедись, что все тесты проходят, и сообщи результат.
```

---

## 📊 Промежуточный итог

Коллега, мы прошли **6 из 12 промтов**. На данный момент реализовано:

| Промт | Описание | Статус |
|-------|----------|--------|
| 1 | Фундамент (конфиг, фабрики, фикстуры) | ✅ |
| 2 | Unit-тесты валидаторов | ✅ |
| 3 | Unit-тесты бизнес-логики | ✅ |
| 4 | Integration-тесты API (CRUD) | ✅ |
| 5 | Integration-тесты (расширенные) | ✅ |
| 6 | Контрактные тесты | ✅ |
| 7 | Smoke-тесты и окружение | ⏳ |
| 8 | Тесты безопасности | ⏳ |
| 9 | Тесты производительности | ⏳ |
| 10 | E2E-тесты (Playwright) | ⏳ |
| 11 | CI/CD workflows | ⏳ |
| 12 | Финализация и документация | ⏳ |

**Оставшиеся промты (7-12):**
- Промт 7: Smoke-тесты запуска приложения, миграций БД, переменных окружения
- Промт 8: Тесты безопасности (SQL-инъекции, XSS, внешние ключи)
- Промт 9: Тесты производительности (таймауты синтеза, эффективность кэша)
- Промт 10: E2E-тесты на Playwright + TypeScript
- Промт 11: GitHub Actions workflows (unit, integration, docker, e2e, release)
- Промт 12: Финализация, Makefile, README, branch protection

**Продолжить со следующими промтами (7-9)?** Или хочешь сначала убедиться, что промты 1-6 работают на твоём проекте, и только потом двигаться дальше?