from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

# ================================
# Models
# ================================
@dataclass
class TokenMetadata:
    user_id: str
    email: str
    role: str = "authenticated"
    person_id: Optional[str] = None
    person_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    person_name: Optional[str] = None


class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    person_id: Optional[str] = None
    person_name: Optional[str] = None


# ================================
# JWT Key Cache
# ================================
class JwksKeyCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[tuple[str, str], tuple[dict, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, kid: str, alg: str = "ES256") -> Optional[dict]:
        key = (kid, alg)
        if key in self._cache:
            jwk_data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return jwk_data
            del self._cache[key]
        return None

    def set(self, kid: str, jwk_data: dict, alg: str = "ES256"):
        self._cache[(kid, alg)] = (jwk_data, datetime.now())

    def clear(self):
        self._cache.clear()