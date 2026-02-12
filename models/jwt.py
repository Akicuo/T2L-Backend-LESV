"""
JWT key cache implementation
"""
from datetime import datetime, timedelta
from typing import Optional


class JwksKeyCache:
    """In-memory cache for JWKS public keys with TTL"""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[tuple[str, str], tuple[dict, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, kid: str, alg: str = "ES256") -> Optional[dict]:
        """Get cached key if still valid"""
        key = (kid, alg)
        if key in self._cache:
            jwk_data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return jwk_data
            del self._cache[key]
        return None

    def set(self, kid: str, jwk_data: dict, alg: str = "ES256"):
        """Cache a key with current timestamp"""
        self._cache[(kid, alg)] = (jwk_data, datetime.now())

    def clear(self):
        """Clear all cached keys"""
        self._cache.clear()
