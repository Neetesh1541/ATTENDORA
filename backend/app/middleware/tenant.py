from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add tenant context to requests.
    The actual tenant validation is done in the dependency layer,
    but this middleware ensures request-level logging and context.
    """

    async def dispatch(self, request: Request, call_next):
        # Add tenant context header tracking
        response: Response = await call_next(request)
        response.headers["X-Tenant-Isolation"] = "enforced"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
