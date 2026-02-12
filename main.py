"""
Time2Log User Backend - FastAPI Implementation
A simpler, shorter Python equivalent to the Java Spring Boot backend.
"""
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.user import TokenMetadata
from services.jwt_service import JwtService
from utils.cookies import get_token_from_cookie

# Import routers
from api.auth import router as auth_router
from api.admin import router as admin_router
from api.health import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================
# FastAPI App
# ================================
app = FastAPI(
    title="Time2Log User Backend",
    description="Authentication service using Supabase",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(health_router)


# ================================
# Dependencies
# ================================
async def require_auth(
    token = Depends(get_token_from_cookie),
) -> TokenMetadata:
    """Require authenticated user"""
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")

    metadata = await JwtService.validate_token(token)
    if not metadata:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid token")

    return metadata


def require_role(*roles: str):
    """Require specific role(s)"""
    async def role_checker(metadata: TokenMetadata = Depends(require_auth)) -> TokenMetadata:
        from fastapi import HTTPException
        if metadata.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return metadata
    return role_checker


# ================================
# Lifespan Event
# ================================
@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info(f"Starting {app.title} v{app.version}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Supabase URL: {settings.SUPABASE_URL[:30]}...")
    logger.info("✅ All systems initialized")


# ================================
# Main Entry Point
# ================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.PORT,
        log_level="info"
    )
