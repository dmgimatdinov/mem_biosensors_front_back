"""
Smoke-тесты переменных окружения.
Проверяют, что приложение корректно читает конфигурацию из env.
"""

import importlib
import logging
import os

import pytest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


@pytest.mark.smoke
class TestEnvironmentVariables:
    """Тесты переменных окружения."""

    def test_database_url_env_var_read(self, tmp_path, monkeypatch):
        """Приложение читает DATABASE_URL из окружения."""
        db_path = tmp_path / "env_test.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        assert main_module.DATABASE_PATH == str(db_path)

    def test_default_database_url_used_when_not_set(self, monkeypatch):
        """При отсутствии DATABASE_URL используется дефолтный путь."""
        monkeypatch.delenv("DATABASE_URL", raising=False)

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        assert main_module.DATABASE_PATH == "memristive_biosensor.db"

    def test_log_level_env_var(self, monkeypatch):
        """LOG_LEVEL влияет на уровень логирования."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        assert main_module._resolve_log_level() == logging.DEBUG

    def test_invalid_log_level_falls_back_to_info(self, monkeypatch):
        """Невалидный LOG_LEVEL приводит к INFO."""
        monkeypatch.setenv("LOG_LEVEL", "INVALID_LEVEL")

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        assert main_module._resolve_log_level() == logging.INFO

    def test_cors_origins_env_var(self, monkeypatch):
        """CORS_ORIGINS читается из окружения."""
        monkeypatch.setenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8000",
        )

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        cors_entries = [m for m in main_module.app.user_middleware if m.cls == CORSMiddleware]
        assert cors_entries, "CORSMiddleware is not configured"
        assert cors_entries[0].kwargs["allow_origins"] == [
            "http://localhost:3000",
            "http://localhost:8000",
        ]

    def test_environment_variables_dont_leak(self, monkeypatch):
        """Секретные переменные не попадают в health-ответ."""
        monkeypatch.setenv("SECRET_KEY", "super_secret_value_12345")

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        client = TestClient(main_module.app)
        response = client.get("/api/health")

        assert response.status_code == 200
        assert "super_secret_value_12345" not in response.text

    def test_app_works_with_minimal_env(self, tmp_path, monkeypatch):
        """Приложение работает с минимальным набором переменных."""
        for key in list(os.environ.keys()):
            if key.startswith("DATABASE") or key.startswith("LOG") or key.startswith("CORS"):
                monkeypatch.delenv(key, raising=False)

        db_path = tmp_path / "minimal.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

        main_module = importlib.import_module("main")
        main_module = importlib.reload(main_module)

        assert main_module.app is not None
        assert main_module.DATABASE_PATH == str(db_path)
