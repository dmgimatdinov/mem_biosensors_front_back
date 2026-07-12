.PHONY: help install install-e2e test test-fast test-unit test-integration test-contract \
	test-security test-performance test-e2e test-all test-everything coverage lint \
	format format-check docker-build docker-run docker-stop docker-test ci-local clean release

PYTHON ?= python
PIP ?= $(PYTHON) -m pip

# Colors for pretty output (safe fallback when tput is unavailable)
GREEN := $(shell command -v tput >/dev/null 2>&1 && tput -Txterm setaf 2 || echo '')
YELLOW := $(shell command -v tput >/dev/null 2>&1 && tput -Txterm setaf 3 || echo '')
RESET := $(shell command -v tput >/dev/null 2>&1 && tput -Txterm sgr0 || echo '')

help: ## Показать эту помощь
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} { \
		if (/^[a-zA-Z0-9_.-]+:.*?##.*$$/) {printf "  ${YELLOW}%-20s${RESET} ${GREEN}%s${RESET}\n", $$1, $$2} \
		else if (/^## .*$$/) {printf "  ${GREEN}%s${RESET}\n", substr($$1,4)} \
	}' $(MAKEFILE_LIST)

## Installation
install: ## Установить зависимости backend
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	$(PIP) install -r backend/requirements-dev.txt
	@echo "✅ Dependencies installed"

install-e2e: ## Установить зависимости для E2E тестов
	cd e2e && npm install
	@if [ "$(OS)" = "Windows_NT" ]; then \
		cd e2e && npx playwright install chromium; \
	elif [ "$(shell uname -s)" = "Darwin" ]; then \
		cd e2e && npx playwright install chromium; \
	else \
		cd e2e && npx playwright install --with-deps chromium; \
	fi
	@echo "✅ E2E dependencies installed"

## Testing
test: test-all ## Алиас для запуска основного набора тестов

test-fast: ## Запустить быстрые тесты (smoke + unit)
	pytest backend/tests/smoke/ backend/tests/unit/ \
		-v -m "smoke or unit" -n auto --tb=short

test-unit: ## Запустить только unit тесты
	pytest backend/tests/unit/ -v -m unit -n auto --tb=short

test-integration: ## Запустить integration тесты
	pytest backend/tests/integration/ -v -m integration -n auto --tb=short

test-contract: ## Запустить contract тесты
	pytest backend/tests/contract/ -v -m contract --tb=short

test-security: ## Запустить security тесты
	pytest backend/tests/security/ -v -m security -n auto --tb=short

test-performance: ## Запустить performance тесты (медленно!)
	pytest backend/tests/performance/ -v -m performance --tb=short --durations=0

test-e2e: ## Запустить E2E тесты (требует Docker)
	cd e2e && npm test

test-all: ## Запустить все тесты (кроме performance и e2e)
	pytest backend/tests/ -v -m "not performance and not e2e" -n auto --tb=short

test-everything: ## Запустить ВСЕ тесты (включая performance и e2e)
	$(MAKE) test-all
	$(MAKE) test-performance
	$(MAKE) test-e2e

## Coverage
coverage: ## Запустить тесты с отчётом о покрытии
	pytest backend/tests/unit/ backend/tests/integration/ \
		-v -n auto \
		--cov=backend \
		--cov-config=.coveragerc \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-fail-under=70
	@echo "📊 HTML coverage report: htmlcov/index.html"

## Code Quality
lint: ## Запустить линтеры (flake8, mypy)
	flake8 backend/ --max-line-length=127 --max-complexity=10 --statistics
	mypy backend/ --ignore-missing-imports --no-strict-optional

format: ## Форматировать код (black)
	black backend/ --line-length 127

format-check: ## Проверить форматирование
	black backend/ --check --line-length 127

## Docker
docker-build: ## Собрать Docker образ
	docker build -t app:latest .

docker-run: ## Запустить Docker контейнер
	docker run -d --name app -p 8080:8000 app:latest
	@echo "🚀 App running at http://localhost:8080"

docker-stop: ## Остановить Docker контейнер
	docker stop app || true
	docker rm app || true

docker-test: ## Собрать образ и запустить smoke тесты
	$(MAKE) docker-build
	docker run -d --name test-app -p 8080:8000 app:latest
	@echo "Testing health endpoint..."
	@timeout=60; interval=2; elapsed=0; \
	while [ $$elapsed -lt $$timeout ]; do \
		if command -v curl >/dev/null 2>&1; then \
			curl -fsS http://localhost:8080/api/health | grep -q '"status"' && echo "✅ Health OK" && break; \
		else \
			wget -qO- http://localhost:8080/api/health | grep -q '"status"' && echo "✅ Health OK" && break; \
		fi; \
		echo "Waiting for app... ($$elapsed/$$timeout seconds)"; \
		sleep $$interval; \
		elapsed=$$((elapsed + interval)); \
		if [ $$elapsed -ge $$timeout ]; then echo "❌ Health FAILED"; docker logs test-app; docker stop test-app || true; docker rm test-app || true; exit 1; fi; \
	done
	@docker stop test-app || true
	@docker rm test-app || true

## CI
ci-local: ## Запустить CI локально (требует act)
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Install: https://github.com/nektos/act"; exit 1; }
	act -j unit-tests

## Cleanup
clean: ## Очистить временные файлы
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name "coverage.xml" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf e2e/test-results/
	rm -rf e2e/playwright-report/
	@echo "🧹 Cleaned"

## Release
release: ## Подготовить релиз (проверить все тесты)
	@echo "🔍 Running all tests..."
	$(MAKE) test-all
	@echo ""
	@echo "✅ All tests passed!"
	@echo ""
	@echo "To create a release:"
	@echo "  1. Update version in pyproject.toml or setup.py"
	@echo "  2. git tag v1.0.0"
	@echo "  3. git push origin v1.0.0"
	@echo "  4. GitHub Actions will build and publish Docker image"