"""
Time2Log User Backend - FastAPI Implementation
A simpler, shorter Python equivalent to the Java Spring Boot backend.
"""
import os
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

import httpx
from fastapi import FastAPI, HTTPException, Request, Response, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from jose import jwt, jwk
from jose.exceptions import JWTError
from pydantic_settings import BaseSettings
from supabase import create_client, Client

from config.config import Settings

from models.main import JwksKeyCache, TokenMetadata, LoginRequest, LoginResponse, TokenValidationResponse
from services.services import JwtService, SupabaseAuthService

settings = Settings()

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
SUPABASE_AUTH_URL = f"{settings.SUPABASE_URL}/auth/v1"







key_cache = JwksKeyCache()


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


# ================================
# Cookie Utilities
# ================================
def create_auth_cookie(token: str) -> dict:
    is_prod = settings.ENVIRONMENT == "production"
    return {
        "key": settings.COOKIE_NAME,
        "value": token,
        "httponly": True,
        "secure": is_prod,
        "samesite": "none" if is_prod else "lax",
        "max_age": 3600 * 24 * 7,  # 7 days
    }


def clear_auth_cookie() -> dict:
    return {
        "key": settings.COOKIE_NAME,
        "value": "",
        "httponly": True,
        "secure": settings.ENVIRONMENT == "production",
        "samesite": "none" if settings.ENVIRONMENT == "production" else "lax",
        "max_age": 0,
        "expires": 0,
    }


# ================================
# Dependencies
# ================================
async def get_token_from_cookie(
    request: Request,
    token: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
) -> Optional[str]:
    if token:
        return token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def require_auth(
    token: Optional[str] = Depends(get_token_from_cookie),
) -> TokenMetadata:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    metadata = await JwtService.validate_token(token)
    if not metadata:
        raise HTTPException(status_code=401, detail="Invalid token")

    return metadata


def require_role(*roles: str):
    async def role_checker(metadata: TokenMetadata = Depends(require_auth)) -> TokenMetadata:
        if metadata.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return metadata
    return role_checker


# ================================
# Routes
# ================================
@app.post("/api/login", response_model=LoginResponse)
async def login(req: LoginRequest, response: Response):
    """Authenticate user with Supabase and set HTTP-only cookie"""
    result = await SupabaseAuthService.login(req.email, req.password)
    access_token = result.get("access_token")

    user_data = await SupabaseAuthService.get_user(access_token)
    user_metadata = user_data.get("user_metadata", {})

    response.set_cookie(**create_auth_cookie(access_token))

    return LoginResponse(
        access_token=access_token,
        user_id=user_data["id"],
        email=user_data["email"],
        role=user_data.get("app_metadata", {}).get("role", "authenticated"),
        person_name=user_metadata.get("person_name"),
    )


@app.get("/api/verify-token", response_model=TokenValidationResponse)
async def verify_token(
    token: Optional[str] = Depends(get_token_from_cookie),
):
    """Validate JWT token from cookie"""
    if not token:
        return TokenValidationResponse(valid=False)

    metadata = await JwtService.validate_token(token)
    if not metadata:
        return TokenValidationResponse(valid=False)

    return TokenValidationResponse(
        valid=True,
        user_id=metadata.user_id,
        email=metadata.email,
        role=metadata.role,
        person_id=metadata.person_id,
        person_name=metadata.person_name,
    )


@app.post("/api/logout")
async def logout(response: Response):
    """Clear authentication cookie"""
    response.delete_cookie(**clear_auth_cookie())
    return {"message": "Logged out successfully"}


@app.post("/api/auth/validate")
async def validate_auth_header(authorization: Optional[str] = None):
    """Legacy endpoint for Bearer token validation (backward compatibility)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[7:]
    metadata = await JwtService.validate_token(token)
    if not metadata:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "valid": True,
        "user_id": metadata.user_id,
        "email": metadata.email,
        "role": metadata.role,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/admin/schemas")
async def get_schemas():
    """Discover all schemas and tables - for testing/admin purposes"""
    print("SCHEMA ENDPOINT CALLED")
    import io
    import sys

    # Capture print output
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        await discover_database_schemas()
        output = buffer.getvalue()
    except Exception as e:
        output = f"Error: {e}"
    finally:
        sys.stdout = old_stdout

    return {"output": output, "timestamp": datetime.now().isoformat()}


@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Test endpoint working", "timestamp": datetime.now().isoformat()}


# ================================
# Main Entry Point
# ================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
