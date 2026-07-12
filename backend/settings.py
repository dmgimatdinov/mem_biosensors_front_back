import os


DEFAULT_METRICS_VERSION = "v1"
_ALLOWED_METRICS_VERSIONS = {"v1", "v2"}


def get_metrics_version() -> str:
    raw = os.getenv("METRICS_VERSION", DEFAULT_METRICS_VERSION).strip().lower()
    return raw if raw in _ALLOWED_METRICS_VERSIONS else DEFAULT_METRICS_VERSION


METRICS_VERSION = get_metrics_version()
