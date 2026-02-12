"""
JWT validation service using Supabase JWKS
"""
import logging
from typing import Optional

import httpx
import hashlib
from jose import jwt, jwk
from jose.exceptions import JWTError
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

from config import settings
from models.user import TokenMetadata
from models.jwt import JwksKeyCache

logger = logging.getLogger(__name__)

# Global key cache
key_cache = JwksKeyCache()


class JwtService:
    """JWT validation using Supabase JWKS"""

    @staticmethod
    async def fetch_jwks() -> dict:
        """Fetch JWKS from Supabase"""
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
        """Validate JWT token and return metadata"""
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
                    logger.warning(f"Key ID {kid} not found in JWKS")
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

        except (JWTError, Exception) as e:
            logger.warning(f"Token validation failed: {e}")
            return None
