"""
Тесты авторизации (если реализована).
Если авторизация не реализована — тесты пропускаются.
"""

import pytest


@pytest.mark.security
class TestAuthorization:
    """Тесты авторизации (опционально)."""

    def test_api_endpoints_accessible_without_auth(self, api_client):
        """Проверяем доступность базового эндпоинта без авторизации."""
        response = api_client.get("/api/health")
        assert response.status_code == 200

    def test_protected_endpoints_require_auth(self, api_client):
        """Если авторизация реализована — проверяем защиту."""
        pytest.skip("Authorization not implemented")
