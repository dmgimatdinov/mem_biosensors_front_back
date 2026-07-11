"""
Smoke-тесты запуска приложения.
Эти тесты гарантируют, что приложение вообще способно стартовать.
Они должны выполняться ПЕРВЫМИ в CI.
"""

import importlib

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


@pytest.mark.smoke
class TestAppStartup:
    """Тесты инициализации приложения."""

    def test_main_module_imports(self):
        """Модуль main импортируется без ошибок."""
        module = importlib.import_module("main")
        assert module is not None

    def test_fastapi_app_instance_exists(self):
        """Экземпляр FastAPI создаётся."""
        main_module = importlib.import_module("main")
        assert isinstance(main_module.app, FastAPI), "app is not a FastAPI instance"

    def test_app_has_title(self):
        """Приложение имеет заголовок (для документации)."""
        main_module = importlib.import_module("main")
        assert main_module.app.title
        assert len(main_module.app.title) > 0

    def test_all_services_initialized_on_startup(self, tmp_path, monkeypatch):
        """После startup все ключевые сервисы инициализированы (не None)."""
        db_path = tmp_path / "startup_services.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        with TestClient(main_module.app):
            pass

        assert main_module.db_manager is not None
        assert main_module.biosensor_service is not None
        assert main_module.passport_service is not None
        assert main_module.analytics_service is not None
        assert main_module.export_service is not None
        assert main_module.combination_service is not None

    def test_routes_registered(self):
        """Все ожидаемые маршруты зарегистрированы."""
        main_module = importlib.import_module("main")
        routes = [route.path for route in main_module.app.routes if hasattr(route, "path")]

        expected_routes = [
            "/api/health",
            "/api/analytes",
            "/api/bio-recognition",
            "/api/immobilization",
            "/api/memristive",
        ]

        for expected in expected_routes:
            assert expected in routes, f"Route {expected} not registered. Available: {routes}"

    def test_docs_routes_registered(self):
        """Маршруты документации зарегистрированы."""
        main_module = importlib.import_module("main")
        routes = [route.path for route in main_module.app.routes if hasattr(route, "path")]

        for docs_route in ["/docs", "/redoc", "/openapi.json"]:
            assert docs_route in routes, f"Docs route {docs_route} not registered"

    def test_cors_middleware_configured(self):
        """CORS middleware настроен."""
        main_module = importlib.import_module("main")
        middleware_classes = [m.cls for m in main_module.app.user_middleware]
        assert CORSMiddleware in middleware_classes

    def test_exception_handlers_registered(self):
        """Обработчики исключений зарегистрированы."""
        main_module = importlib.import_module("main")
        assert len(main_module.app.exception_handlers) > 0

    def test_app_does_not_crash_on_startup(self, tmp_path, monkeypatch):
        """Приложение стартует без исключений."""
        db_path = tmp_path / "startup_test.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        with TestClient(main_module.app):
            assert main_module.app is not None
