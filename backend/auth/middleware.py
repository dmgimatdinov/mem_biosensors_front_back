from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import settings


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Attach lightweight auth mode context for observability and optional downstream use."""

    async def dispatch(self, request: Request, call_next):
        request.state.auth_mode = settings.AUTH_MODE
        response: Response = await call_next(request)
        return response
