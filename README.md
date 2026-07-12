# Memristive Biosensors Passport Manager

[![Unit Tests](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-unit-tests.yml/badge.svg)](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-unit-tests.yml)
[![Integration Tests](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-integration.yml/badge.svg)](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-integration.yml)
[![Docker Build](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-docker-build.yml/badge.svg)](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-docker-build.yml)
[![E2E Tests](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-e2e.yml/badge.svg)](https://github.com/dmgimatdinov/mem_biosensors_front_back/actions/workflows/ci-e2e.yml)
[![codecov](https://codecov.io/gh/dmgimatdinov/mem_biosensors_front_back/branch/main/graph/badge.svg)](https://codecov.io/gh/dmgimatdinov/mem_biosensors_front_back)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Система управления паспортами мемристивных биосенсоров.

## 🚀 Быстрый старт

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/dmgimatdinov/mem_biosensors_front_back.git
cd mem_biosensors_front_back

# Установить зависимости
make install

# Запустить приложение
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Собрать образ
make docker-build

# Запустить контейнер
make docker-run

# Остановить контейнер
make docker-stop
```

Приложение будет доступно по адресу: http://localhost:8080

## 🧪 Тестирование

### Быстрые команды

```bash
# Показать все доступные команды
make help

# Запустить быстрые тесты (smoke + unit)
make test-fast

# Запустить все тесты (кроме performance и e2e)
make test-all

# Запустить тесты с отчётом о покрытии
make coverage
```

### Типы тестов

| Тип | Команда | Время | Описание |
|---|---|---|---|
| Smoke + Unit | `make test-fast` | <10s | Проверка запуска, миграций, базовой логики |
| Unit | `make test-unit` | <30s | Валидаторы, бизнес-логика, сервисы |
| Integration | `make test-integration` | <60s | API endpoints, CRUD |
| Contract | `make test-contract` | <30s | Схемы API, маппинг полей |
| Security | `make test-security` | <60s | SQL-инъекции, XSS, целостность |
| Performance | `make test-performance` | 1-5 min | Таймауты, кэш, нагрузка |
| E2E | `make test-e2e` | 1-2 min | Playwright (требует Docker) |

### Покрытие кода

```bash
# Запустить тесты с покрытием
make coverage

# Открыть HTML отчёт (macOS)
open htmlcov/index.html

# Открыть HTML отчёт (Linux)
xdg-open htmlcov/index.html
```

Минимальное покрытие: 70%

### E2E тесты

E2E тесты запускаются против Docker-контейнера.

```bash
# Установить зависимости для E2E
make install-e2e

# Запустить E2E тесты
make test-e2e
```

## 📊 CI/CD

### Workflows

- Unit Tests: запускаются на push и PR (smoke + unit)
- Integration Tests: запускаются на PR (integration + contract + security)
- Docker Build: собирает образ и проверяет smoke-тесты
- E2E Tests: запускаются ночью, вручную и на теги релизов
- Release: публикует Docker-образ в GHCR по тегу

### Branch Protection (рекомендуется для `main`)

- Требуется passing CI (unit + integration + docker)
- Требуется минимум 1 approval
- Запрещены force push и deletion

## 🛠 Разработка

### Код-стайл

```bash
# Проверить линтеры
make lint

# Форматировать код
make format

# Проверить форматирование
make format-check
```

### Локальный CI

```bash
# Запустить CI локально (требует act)
make ci-local
```

## ☁️ Deploy to Cloudflare Pages

### Prerequisites

- Аккаунт Cloudflare
- Репозиторий на GitHub

### Steps

1. Выполнить `git push origin main`
2. В Cloudflare Pages подключить репозиторий
3. Указать build command: `bash build.sh`
4. Указать build output directory: `dist`

Локальная сборка (как в CI):

```bash
bash build.sh
```

## 📁 Структура проекта

```text
.
├── backend/
│   ├── main.py                 # FastAPI приложение
│   ├── domain/                 # Бизнес-логика
│   ├── db/                     # Работа с БД
│   ├── services/               # Сервисы
│   └── tests/                  # Тесты
│       ├── smoke/
│       ├── unit/
│       ├── integration/
│       ├── contract/
│       ├── security/
│       └── performance/
├── e2e/                        # E2E тесты (Playwright)
├── .github/workflows/          # GitHub Actions
├── docs/TESTING_GUIDE.md       # Руководство по тестированию
├── Makefile                    # Команды для разработки и тестирования
└── README.md                   # Этот файл
```

## 📝 Лицензия

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`make test-all`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📞 Поддержка

- Откройте issue в GitHub
- См. документацию в `backend/docs/` и `docs/TESTING_GUIDE.md`
