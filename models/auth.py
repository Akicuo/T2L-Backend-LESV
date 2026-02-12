"""
Authentication-related Pydantic models
"""
from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    person_name: Optional[str] = None


class TokenValidationResponse(BaseModel):
    """Token validation response model"""
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    person_id: Optional[str] = None
    person_name: Optional[str] = None
