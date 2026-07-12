# Руководство по тестированию

## Для разработчиков

### Добавление нового теста

1. Определите тип теста:
- Unit: для бизнес-логики (быстрый, <1s)
- Integration: для API endpoints (<5s)
- Contract: для схем API (<1s)
- Security: для безопасности (<2s)
- Performance: для производительности (может быть медленным)

2. Создайте файл в соответствующей директории:
- `backend/tests/unit/test_my_feature.py`
- `backend/tests/integration/test_my_endpoint.py`

3. Используйте фабрики из `backend/tests/factories.py`:

```python
from backend.tests.factories import make_analyte


def test_my_feature():
    data = make_analyte(ta_name="Test")
    assert data["ta_name"] == "Test"
```

4. Пометьте тест маркером:

```python
import pytest


@pytest.mark.unit
def test_my_feature():
    assert True
```

### Запуск тестов

```bash
# Быстрые тесты (перед коммитом)
make test-fast

# Все тесты (перед PR)
make test-all

# Конкретный файл
pytest backend/tests/unit/test_my_feature.py -v
```

## Для QA

### Пирамида тестов

```text
        /\
       /E2E\              <- 5%   (Playwright)
      /------\
     /Security\           <- 10%  (SQL injection, XSS)
    /----------\
   /Integration\          <- 25%  (API endpoints)
  /------------\
 / Contract Tests \       <- 15%  (API schemas)
/------------------\
/    Unit tests     \     <- 40%  (validators, services)
/--------------------\
/ Smoke & Performance \   <- 5%   (startup, timeouts)
/----------------------\
```

### Что тестировать

Unit-тесты:
- Валидаторы (все поля, все диапазоны)
- Бизнес-логика (синтез комбинаций, расчёт метрик)
- Сервисы (CRUD, экспорт, аналитика)

Integration-тесты:
- Все API endpoints (GET, POST, PUT, DELETE)
- HTTP-статусы (200, 400, 404, 409, 422, 500)
- CORS-заголовки
- Пагинация

Contract-тесты:
- Схемы ответов (Pydantic модели)
- Маппинг полей (PascalCase)
- Форматы данных

Security-тесты:
- SQL-инъекции (все входные точки)
- XSS-пейлоады
- Экстремальные данные (длинные строки, unicode)
- Целостность данных (внешние ключи)

Performance-тесты:
- Таймауты синтеза (1000, 10000 комбинаций)
- Эффективность кэша
- Время ответа API

E2E-тесты:
- Полные пользовательские сценарии
- Навигация между страницами
- Создание данных через UI
- Связь фронтенд-бэкенд

### Отчёты

```bash
# Покрытие кода
make coverage
xdg-open htmlcov/index.html

# Длительность тестов
pytest backend/tests/ --durations=10

# E2E отчёт
cd e2e && npm run test:report
```

## Для DevOps

### CI/CD Pipeline

`Push -> Unit Tests -> Integration Tests -> Docker Build -> (E2E nightly)`

### Мониторинг

- Codecov: https://codecov.io/gh/dmgimatdinov/mem_biosensors_front_back
- GitHub Actions: https://github.com/dmgimatdinov/mem_biosensors_front_back/actions

### Алерты

- Если unit тесты падают: блокируется merge/push по правилам branch protection
- Если integration тесты падают: блокируется PR
- Если Docker build падает: блокируется PR
- Если E2E тесты падают: опциональный алерт в Slack