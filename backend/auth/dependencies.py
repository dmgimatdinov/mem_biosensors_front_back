from typing import Optional

from fastapi import Depends, HTTPException, Request

import settings
from auth.rbac import has_role_or_system
from auth.service import AuthService, Principal


def get_auth_service(request: Request) -> AuthService:
    service = getattr(request.app.state, "auth_service", None)
    if service is None or getattr(service, "auth_mode", None) != settings.AUTH_MODE:
        service = AuthService()
        request.app.state.auth_service = service
    return service


def get_current_principal(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> Principal:
    authorization = request.headers.get("Authorization")
    api_key = request.headers.get("X-API-Key")
    principal = auth_service.authenticate(authorization, api_key)
    auth_service.enforce_user_rate_limit(principal)
    request.state.principal = principal
    return principal


def require_role(required_role: str):
    def _dependency(
        request: Request,
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if settings.AUTH_MODE == "disabled":
            return principal
        if not has_role_or_system(principal.role, required_role):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal

    return _dependency


def require_synthesis_limit(
    principal: Principal = Depends(get_current_principal),
    auth_service: AuthService = Depends(get_auth_service),
) -> Principal:
    auth_service.enforce_synthesis_rate_limit(principal)
    return principal
