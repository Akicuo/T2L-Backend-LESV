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
        # Supabase JWKS is at /auth/v1/.well-known/jwks.json
        url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
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
            logger.info(f"Validating token, length: {len(token) if token else 0}")

            # Decode header to get kid
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            alg = header.get("alg", "ES256")
            logger.info(f"Token header - kid: {kid}, alg: {alg}")

            # Check cache
            cached_key = key_cache.get(kid, alg)
            if cached_key:
                logger.info(f"Using cached key for kid: {kid}")
                public_key = jwk.construct(cached_key, alg)
            else:
                # Fetch JWKS
                logger.info(f"Fetching JWKS from {settings.SUPABASE_URL}")
                jwks = await cls.fetch_jwks()
                logger.info(f"JWKS fetched, keys count: {len(jwks.get('keys', []))}")

                for key_data in jwks.get("keys", []):
                    if key_data.get("kid") == kid:
                        logger.info(f"Found matching key for kid: {kid}")
                        key_cache.set(kid, key_data, alg)
                        public_key = jwk.construct(key_data, alg)
                        break
                else:
                    logger.warning(f"Key ID {kid} not found in JWKS")
                    return None

            # Verify and decode token
            logger.info("Decoding token with public key...")
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                audience="authenticated",  # Supabase uses "authenticated" as audience
            )
            logger.info(f"Token decoded successfully, sub: {payload.get('sub')}")

            return TokenMetadata(
                user_id=payload.get("sub"),
                email=payload.get("email", ""),
                role=payload.get("role", "authenticated"),
                person_id=payload.get("person_id"),
                person_name=payload.get("person_name"),
            )

        except JWTError as e:
            logger.error(f"JWT validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {type(e).__name__}: {e}")
            return None
