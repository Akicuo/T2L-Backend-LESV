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

# ================================
# Configuration
# ================================
class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    JWT_SECRET: Optional[str] = None
    COOKIE_NAME: str = "supabase-auth-token"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"
    PORT: int = 8080

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
SUPABASE_AUTH_URL = f"{settings.SUPABASE_URL}/auth/v1"


# ================================
# Database Schema Discovery
# ================================
async def discover_database_schemas():
    """Query Supabase to discover all schemas and tables using the REST API"""
    print("\n" + "=" * 60)
    print("DATABASE SCHEMA DISCOVERY")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Query Postgres REST API for schemas and tables
            # Using Supabase's built-in pg_catalog access via PostgREST
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            }

            # Query schemas
            schemas_url = f"{settings.SUPABASE_URL}/rest/v1/rpc/exec"
            schemas_query = "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;"

            # Alternative: Use direct table query to check available tables
            tables_url = f"{settings.SUPABASE_URL}/rest/v1/"
            tables_response = await client.get(tables_url, headers=headers, timeout=10.0)

            print(f"\nSupabase URL: {settings.SUPABASE_URL}")
            print(f"Auth URL: {SUPABASE_AUTH_URL}")
            print(f"Cookie Name: {settings.COOKIE_NAME}")
            print(f"CORS Origins: {settings.CORS_ORIGINS}")
            print(f"Environment: {settings.ENVIRONMENT}")
            print(f"Port: {settings.PORT}")

            # Try to list common tables via PostgREST
            print("\n--- Attempting to discover tables via PostgREST ---")
            common_tables = ["users", "profiles", "tasks", "time_entries", "persons"]
            for table in common_tables:
                try:
                    resp = await client.get(
                        f"{settings.SUPABASE_URL}/rest/v1/{table}?limit=1",
                        headers={**headers, "Prefer": "count=exact"},
                        timeout=5.0
                    )
                    if resp.status_code == 200:
                        count = resp.headers.get("content-range", "").split("/")[-1]
                        print(f"  Table '{table}': EXISTS ({count} rows)")
                    elif resp.status_code == 401:
                        print(f"  Table '{table}': ACCESS DENIED")
                    else:
                        print(f"  Table '{table}': NOT FOUND (status: {resp.status_code})")
                except Exception as e:
                    print(f"  Table '{table}': ERROR - {e}")

            print("\n--- Checking Supabase Auth Tables ---")
            # Check auth users via admin API
            try:
                auth_resp = await client.get(
                    f"{SUPABASE_AUTH_URL}/users",
                    headers=headers,
                    timeout=10.0
                )
                if auth_resp.status_code == 200:
                    users = auth_resp.json()
                    if isinstance(users, list):
                        print(f"  Auth users: {len(users)} users found")
                    elif isinstance(users, dict) and "users" in users:
                        print(f"  Auth users: {len(users['users'])} users found")
                else:
                    print(f"  Auth users: Unable to query (status: {auth_resp.status_code})")
            except Exception as e:
                print(f"  Auth users: ERROR - {e}")

    except Exception as e:
        print(f"Schema discovery failed: {e}")

    print("=" * 60 + "\n")


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


key_cache = JwksKeyCache()


# ================================
# Services
# ================================
class JwtService:
    """JWT validation using Supabase JWKS"""

    @staticmethod
    async def fetch_jwks() -> dict:
        url = f"{settings.SUPABASE_URL}/.well-known/jwks.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def p256_public_key(x: str, y: str) -> str:
        """Convert P-256 coordinates to PEM format"""
        x_bytes = bytes.fromhex(x)
        y_bytes = bytes.fromhex(y)
        public_key = ec.EllipticCurvePublicNumbers(
            x=int.from_bytes(x_bytes, 'big'),
            y=int.from_bytes(y_bytes, 'big'),
            curve=ec.SECP256R1()
        ).public_key(default_backend())
        return public_key.public_bytes(
            encoding=hashlib.sha256,
            format=hashlib.sha256
        ).hex()

    @classmethod
    async def validate_token(cls, token: str) -> Optional[TokenMetadata]:
        try:
            # Decode header to get kid
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            alg = header.get("alg", "ES256")

            # Check cache
            cached_key = key_cache.get(kid, alg)
            if cached_key:
                public_key = jwk.construct(cached_key, alg)
            else:
                # Fetch JWKS
                jwks = await cls.fetch_jwks()
                for key_data in jwks.get("keys", []):
                    if key_data.get("kid") == kid:
                        key_cache.set(kid, key_data, alg)
                        public_key = jwk.construct(key_data, alg)
                        break
                else:
                    return None

            # Verify and decode token
            payload = jwt.decode(token, public_key, algorithms=[alg])
            return TokenMetadata(
                user_id=payload.get("sub"),
                email=payload.get("email", ""),
                role=payload.get("role", "authenticated"),
                person_id=payload.get("person_id"),
                person_name=payload.get("person_name"),
            )

        except (JWTError, Exception):
            return None


class SupabaseAuthService:
    """Supabase authentication client"""

    @staticmethod
    async def login(email: str, password: str) -> dict:
        url = f"{SUPABASE_AUTH_URL}/token?grant_type=password"
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Content-Type": "application/json",
        }
        payload = {"email": email, "password": password}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)

            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            return response.json()

    @staticmethod
    async def get_user(token: str) -> dict:
        url = f"{SUPABASE_AUTH_URL}/user"
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def logout(token: str) -> None:
        url = f"{SUPABASE_AUTH_URL}/logout"
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {token}",
        }

        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers, timeout=10.0)


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


@app.on_event("startup")
async def startup_event():
    """Run database schema discovery on startup"""
    await discover_database_schemas()


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
