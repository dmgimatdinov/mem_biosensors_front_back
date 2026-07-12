import os
import sys


DEFAULT_METRICS_VERSION = "v1"
_ALLOWED_METRICS_VERSIONS = {"v1", "v2"}


def get_metrics_version() -> str:
    raw = os.getenv("METRICS_VERSION", DEFAULT_METRICS_VERSION).strip().lower()
    return raw if raw in _ALLOWED_METRICS_VERSIONS else DEFAULT_METRICS_VERSION


METRICS_VERSION = get_metrics_version()


def _is_test_env() -> bool:
    return (
        os.getenv("PYTEST_CURRENT_TEST") is not None
        or os.getenv("PYTEST_XDIST_WORKER") is not None
        or os.getenv("TESTING", "0") == "1"
        or "pytest" in sys.modules
    )


DEFAULT_AUTH_MODE = "disabled" if _is_test_env() else "jwt"
_ALLOWED_AUTH_MODES = {"disabled", "jwt"}


def get_auth_mode() -> str:
    raw = os.getenv("AUTH_MODE", DEFAULT_AUTH_MODE).strip().lower()
    return raw if raw in _ALLOWED_AUTH_MODES else DEFAULT_AUTH_MODE


AUTH_MODE = get_auth_mode()
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-jwt-secret-change-me")
JWT_ACCESS_TTL_SECONDS = int(os.getenv("JWT_ACCESS_TTL_SECONDS", "900"))
JWT_REFRESH_TTL_SECONDS = int(os.getenv("JWT_REFRESH_TTL_SECONDS", "604800"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_USER_PER_MIN = int(os.getenv("RATE_LIMIT_USER_PER_MIN", "100"))
RATE_LIMIT_SYNTHESIS_PER_HOUR = int(os.getenv("RATE_LIMIT_SYNTHESIS_PER_HOUR", "10"))
