"""
Health check routes
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Request, Cookie
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# Backward compatibility with /api/health path
@router.get("/api/health")
async def health_check_api():
    """Health check endpoint at /api/health (for backward compatibility)"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "Test endpoint working",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/debug/cookies")
async def debug_cookies(
    request: Request,
    token: str | None = Cookie(None, alias=settings.COOKIE_NAME),
):
    """Debug endpoint to see what cookies are being received"""
    logger.info(f"Debug cookies - All cookies: {request.cookies}")
    logger.info(f"Debug cookies - Token from Cookie(): {token is not None}")

    return {
        "all_cookies": request.cookies,
        "cookie_name_setting": settings.COOKIE_NAME,
        "token_present": token is not None,
        "token_preview": token[:50] + "..." if token else None,
    }


@router.get("/debug/settings")
async def debug_settings():
    """Debug endpoint to see current settings"""
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "COOKIE_NAME": settings.COOKIE_NAME,
        "SUPABASE_URL": settings.SUPABASE_URL[:50] + "..." if settings.SUPABASE_URL else None,
    }
