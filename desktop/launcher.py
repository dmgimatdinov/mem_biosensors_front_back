"""Desktop launcher for the Memristive Biosensors portable application."""

from __future__ import annotations

import io
import logging
import os
import secrets
import socket
import sys
import threading
import time
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(sys._MEIPASS).resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = BASE_DIR

DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
FRONTEND_DIR = BUNDLE_DIR / "frontend"
ASSETS_DIR = BUNDLE_DIR / "assets"
BANNER_PATH = ASSETS_DIR / "banner.txt"
JWT_SECRET_FILE = DATA_DIR / ".jwt_secret"


def _ensure_standard_streams() -> None:
    """Ensure sys.stdout and sys.stderr are valid objects in packaged runs."""
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()


def ensure_runtime_dirs() -> None:
    """Create data and logs folders that the portable build needs."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging() -> logging.Logger:
    """Configure launcher logging to the portable logs directory."""
    ensure_runtime_dirs()
    logger = logging.getLogger("desktop")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


LOGGER = configure_logging()
FIRST_RUN = False


def initialize_environment() -> tuple[bool, str]:
    """Create required runtime directories and environment variables."""
    global FIRST_RUN
    ensure_runtime_dirs()
    os.chdir(BASE_DIR)

    if not JWT_SECRET_FILE.exists():
        secret = secrets.token_urlsafe(32)
        JWT_SECRET_FILE.write_text(secret, encoding="utf-8")
        LOGGER.info("JWT secret generated on first run")
        FIRST_RUN = True
    else:
        secret = JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
        FIRST_RUN = False

    database_path = DATA_DIR / "memristive_biosensor.db"
    os.environ["DATABASE_PATH"] = str(database_path)
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"
    os.environ["AUTH_MODE"] = "jwt"
    os.environ["JWT_SECRET"] = secret
    os.environ["JWT_ACCESS_TTL_SECONDS"] = "900"
    os.environ["JWT_REFRESH_TTL_SECONDS"] = "604800"
    os.environ["REDIS_URL"] = ""
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["CORS_ORIGINS"] = "http://127.0.0.1:8000,http://localhost:8000"
    os.environ["UVICORN_RELOAD"] = "false"

    if not (DATA_DIR / ".jwt_secret").exists():
        LOGGER.warning("JWT secret file is missing; creating a new one")

    return FIRST_RUN, secret


def find_free_port(start: int = 8000, max_tries: int = 12) -> int:
    """Find the first available localhost port in the requested range."""
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found in range {start}-{start + max_tries - 1}")


def open_browser(url: str, delay: int = 2) -> None:
    """Open the default browser after a short delay."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        LOGGER.info("Browser opened: %s", url)
    except Exception as exc:  # pragma: no cover - best effort only
        LOGGER.warning("Failed to open browser automatically: %s", exc)


def print_banner(port: int) -> None:
    """Print the console banner and launch instructions."""
    if BANNER_PATH.exists():
        print(BANNER_PATH.read_text(encoding="utf-8").strip())
    print(f"\n🚀 Server running at: http://127.0.0.1:{port}")
    if FIRST_RUN:
        print("🔑 Default credentials: admin / admin")
        print("⚠️  Change the administrator password after the first login")
    else:
        print("⚠️  Change the administrator password if it is still the default")
    print("⏹  Press Ctrl+C to stop\n")


def prepare_import_paths() -> None:
    """Ensure backend modules can be imported from development and packaged runs."""
    sys.path.insert(0, str(BASE_DIR))
    if (BASE_DIR / "backend").exists():
        sys.path.insert(0, str(BASE_DIR / "backend"))
    if (BUNDLE_DIR / "backend").exists():
        sys.path.insert(0, str(BUNDLE_DIR / "backend"))


def main() -> int:
    """Launch the FastAPI backend and open the UI in the browser."""
    _ensure_standard_streams()
    initialize_environment()
    prepare_import_paths()

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    print_banner(port)

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    try:
        import uvicorn

        uvicorn.run(
            "backend.main:app",
            host="127.0.0.1",
            port=port,
            log_level="info",
            access_log=False,
            log_config=None,
        )
    except KeyboardInterrupt:
        LOGGER.info("Server stopped by user")
        return 0
    except Exception as exc:  # pragma: no cover - runtime path dependent
        LOGGER.exception("Launcher failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
