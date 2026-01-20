"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import settings


def get_client_ip(request: Request) -> str:
    """Get client IP address, considering proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Create limiter with Redis backend in production, memory in development
if settings.is_production:
    limiter = Limiter(
        key_func=get_client_ip,
        storage_uri=settings.redis_url,
        strategy="fixed-window",
    )
else:
    limiter = Limiter(
        key_func=get_client_ip,
        strategy="fixed-window",
    )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "details": {
                "message": f"Rate limit exceeded. {exc.detail}",
                "retry_after": request.state.view_rate_limit.get_retry_after() if hasattr(request.state, 'view_rate_limit') else 60,
            },
        },
    )


# Rate limit presets for different endpoint types
class RateLimits:
    """Predefined rate limits for different endpoint categories."""

    # Authentication endpoints - strict limits to prevent brute force
    AUTH_LOGIN = "5/minute"
    AUTH_SIGNUP = "3/minute"
    AUTH_PASSWORD_RESET = "3/minute"

    # Standard API endpoints
    API_STANDARD = "60/minute"
    API_SEARCH = "30/minute"

    # AI/Generation endpoints - expensive operations
    AI_GENERATE = "10/minute"
    AI_EMBEDDING = "20/minute"

    # Admin endpoints
    ADMIN_STANDARD = "120/minute"

    # Webhooks and callbacks
    WEBHOOK = "100/minute"
