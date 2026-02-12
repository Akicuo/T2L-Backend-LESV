"""
Health check routes
"""
import logging
from datetime import datetime

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
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
