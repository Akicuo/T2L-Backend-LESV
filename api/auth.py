"""
Authentication routes
"""
import logging

from fastapi import APIRouter, HTTPException, Response, Depends, Header

from models.auth import LoginRequest, LoginResponse, TokenValidationResponse
from models.user import TokenMetadata
from services.auth_service import AuthService
from services.jwt_service import JwtService
from services.person_service import PersonService
from utils.cookies import create_auth_cookie, clear_auth_cookie, get_token_from_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, response: Response):
    """Authenticate user with Supabase and set HTTP-only cookie"""
    result = await AuthService.login(req.email, req.password)
    access_token = result.get("access_token")

    user_data = await AuthService.get_user(access_token)
    user_id = user_data["id"]
    user_metadata = user_data.get("user_metadata", {})

    # Try to get person_name from multiple sources:
    # 1. user_metadata.person_name (set during registration)
    # 2. app.persons table lookup by user_id
    # 3. Fallback to email
    person_name = user_metadata.get("person_name")

    if not person_name:
        # Look up person data from app.persons table
        person = await PersonService.get_person_by_user_id(user_id, access_token)
        person_name = person.person_name

    # Final fallback to email if no person_name found
    if not person_name:
        person_name = user_data.get("email", "")

    response.set_cookie(**create_auth_cookie(access_token))

    return LoginResponse(
        access_token=access_token,
        user_id=user_id,
        email=user_data["email"],
        role=user_data.get("app_metadata", {}).get("role", "authenticated"),
        person_name=person_name,
    )


@router.get("/verify-token", response_model=TokenValidationResponse)
async def verify_token(
    token = Depends(get_token_from_cookie),
):
    """Validate JWT token from cookie"""
    logger.info(f"verify-token called, token present: {token is not None}")
    if token:
        logger.info(f"Token preview: {token[:50]}...")

    if not token:
        logger.warning("No token found in cookie or header")
        return TokenValidationResponse(valid=False)

    metadata = await JwtService.validate_token(token)
    if not metadata:
        logger.warning("Token validation failed")
        return TokenValidationResponse(valid=False)

    # Look up person data from app.persons table
    person = await PersonService.get_person_by_user_id(metadata.user_id, token)

    # Use database person data, fallback to JWT claims, then email
    person_id = person.person_id or metadata.person_id
    person_name = person.person_name or metadata.person_name or metadata.email

    return TokenValidationResponse(
        valid=True,
        user_id=metadata.user_id,
        email=metadata.email,
        role=metadata.role,
        person_id=person_id,
        person_name=person_name,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear authentication cookie"""
    # Use set_cookie with an expired value, since our helper returns
    # parameters compatible with Response.set_cookie, not delete_cookie.
    response.set_cookie(**clear_auth_cookie())
    return {"message": "Logged out successfully"}


@router.post("/auth/validate")
async def validate_auth_header(authorization: str | None = Header(None)):
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
