"""
Cookie utilities for authentication
"""
import logging
from typing import Optional

from fastapi import Request, Cookie

from config import settings

logger = logging.getLogger(__name__)


def create_auth_cookie(token: str) -> dict:
    """Create authentication cookie configuration"""
    is_prod = settings.ENVIRONMENT == "production"
    return {
        "key": settings.COOKIE_NAME,
        "value": token,
        "httponly": True,
        "secure": is_prod,
        "samesite": "none" if is_prod else "lax",
        "max_age": 3600 * 24 * 7,  # 7 days
        "path": "/",  # Ensure cookie is sent for all paths
    }


def clear_auth_cookie() -> dict:
    """Create configuration to clear authentication cookie"""
    return {
        "key": settings.COOKIE_NAME,
        "value": "",
        "httponly": True,
        "secure": settings.ENVIRONMENT == "production",
        "samesite": "none" if settings.ENVIRONMENT == "production" else "lax",
        "max_age": 0,
        "expires": 0,
        "path": "/",
    }


async def get_token_from_cookie(
    request: Request,
    token: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
) -> Optional[str]:
    """Extract token from cookie or Authorization header"""
    logger.info(f"get_token_from_cookie - Cookie name: {settings.COOKIE_NAME}")
    logger.info(f"get_token_from_cookie - Token from cookie: {token is not None}")
    logger.info(f"get_token_from_cookie - All cookies: {request.cookies}")

    if token:
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    return None
