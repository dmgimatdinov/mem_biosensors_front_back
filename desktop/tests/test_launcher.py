"""Tests for the portable launcher helpers."""

import importlib.util
import sys
from pathlib import Path

import pytest

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

spec = importlib.util.spec_from_file_location(
    "desktop.launcher",
    repo_root / "launcher.py",
)
launcher_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = launcher_module
spec.loader.exec_module(launcher_module)

find_free_port = launcher_module.find_free_port
initialize_environment = launcher_module.initialize_environment


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("AUTH_MODE", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("JWT_ACCESS_TTL_SECONDS", raising=False)
    monkeypatch.delenv("JWT_REFRESH_TTL_SECONDS", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("UVICORN_RELOAD", raising=False)


def test_find_free_port_returns_open_port(tmp_path):
    port = find_free_port(start=18000, max_tries=3)
    assert isinstance(port, int)
    assert port >= 18000


def test_initialize_environment_creates_runtime_dirs(tmp_path, monkeypatch):
    launcher_module.BASE_DIR = tmp_path
    launcher_module.BUNDLE_DIR = tmp_path
    launcher_module.DATA_DIR = tmp_path / "data"
    launcher_module.LOGS_DIR = tmp_path / "logs"
    launcher_module.JWT_SECRET_FILE = tmp_path / "data" / ".jwt_secret"

    first_run, secret = initialize_environment()

    assert first_run is True
    assert secret
    assert (tmp_path / "data").exists()
    assert (tmp_path / "logs").exists()
    assert (tmp_path / "data" / ".jwt_secret").exists()
