"""
Authentication routes
"""
import logging

from fastapi import APIRouter, HTTPException, Response, Depends

from models.auth import LoginRequest, LoginResponse, TokenValidationResponse
from models.user import TokenMetadata
from services.auth_service import AuthService
from services.jwt_service import JwtService
from utils.cookies import create_auth_cookie, clear_auth_cookie, get_token_from_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, response: Response):
    """Authenticate user with Supabase and set HTTP-only cookie"""
    result = await AuthService.login(req.email, req.password)
    access_token = result.get("access_token")

    user_data = await AuthService.get_user(access_token)
    user_metadata = user_data.get("user_metadata", {})

    response.set_cookie(**create_auth_cookie(access_token))

    return LoginResponse(
        access_token=access_token,
        user_id=user_data["id"],
        email=user_data["email"],
        role=user_data.get("app_metadata", {}).get("role", "authenticated"),
        person_name=user_metadata.get("person_name"),
    )


@router.get("/verify-token", response_model=TokenValidationResponse)
async def verify_token(
    token = Depends(get_token_from_cookie),
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


@router.post("/logout")
async def logout(response: Response):
    """Clear authentication cookie"""
    response.delete_cookie(**clear_auth_cookie())
    return {"message": "Logged out successfully"}


@router.post("/auth/validate")
async def validate_auth_header(authorization: str | None = None):
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
