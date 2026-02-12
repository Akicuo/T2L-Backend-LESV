from config.config import Settings
# ================================
from models.main import TokenMetadata
from typing import Optional
import httpx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from jose import jwt, jwk
from jose.exceptions import JWTError
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
    """Supabase authentication client using the official Python library"""

    @staticmethod
    async def login(email: str, password: str) -> dict:
        """Login using Supabase Python client"""
        try:
            # Use Supabase client to sign in with password
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            # Return session data
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata,
                    "app_metadata": response.user.app_metadata,
                }
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid credentials: {str(e)}")

    @staticmethod
    async def get_user(token: str) -> dict:
        """Get user using Supabase Python client"""
        try:
            # Set the access token for this request
            response = supabase.auth.get_user(token)

            return {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
                "app_metadata": response.user.app_metadata,
                "created_at": response.user.created_at.isoformat() if response.user.created_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    @staticmethod
    async def logout(token: str) -> None:
        """Logout using Supabase Python client"""
        try:
            supabase.auth.sign_out()
        except Exception:
            # Don't raise an error if logout fails
            pass