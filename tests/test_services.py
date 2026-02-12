"""
Service layer tests
"""
import pytest
from unittest.mock import patch

from models.user import TokenMetadata
from services.jwt_service import JwtService, key_cache
from services.auth_service import AuthService
from services.schema_service import SchemaService


@pytest.mark.asyncio
async def test_jwt_service_fetch_jwks(mocker, app):
    """Test JWKS fetching"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "keys": [
            {
                "kid": "test-key",
                "alg": "ES256",
                "kty": "EC",
                "x": "test_x",
                "y": "test_y"
            }
        ]
    }

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    jwks = await JwtService.fetch_jwks()

    assert "keys" in jwks
    assert len(jwks["keys"]) == 1
    assert jwks["keys"][0]["kid"] == "test-key"


@pytest.mark.asyncio
async def test_jwt_service_validate_token_valid(mocker, app):
    """Test token validation with valid token"""
    mock_jwks = {
        "keys": [
            {
                "kid": "key-1",
                "alg": "ES256",
                "kty": "EC",
                "x": "abc123",
                "y": "def456"
            }
        ]
    }

    mocker.patch("services.jwt_service.JwtService.fetch_jwks", return_value=mock_jwks)

    mock_payload = {
        "sub": "user-123",
        "email": "test@example.com",
        "role": "authenticated"
    }

    mocker.patch("jose.jwt.decode", return_value=mock_payload)

    token = "valid.token.here"
    result = await JwtService.validate_token(token)

    assert result is not None
    assert result.user_id == "user-123"
    assert result.email == "test@example.com"
    assert result.role == "authenticated"


@pytest.mark.asyncio
async def test_jwt_service_validate_token_invalid(mocker, app):
    """Test token validation with invalid token"""
    mocker.patch("jose.jwt.decode", side_effect=Exception("Invalid token"))

    token = "invalid.token"
    result = await JwtService.validate_token(token)

    assert result is None


def test_jwt_key_cache(app):
    """Test JWKS key cache TTL"""
    from datetime import datetime, timedelta

    cache = key_cache
    test_key = {"kid": "test", "alg": "ES256"}

    # Test set and get
    cache.set("test", test_key)
    result = cache.get("test")
    assert result == test_key

    # Test expiry (small delay)
    import time
    cache.set("test", test_key)
    time.sleep(0.01)  # Very small delay
    cached = cache.get("test")
    assert cached is not None  # Should still be in cache


def test_jwt_key_cache_clear():
    """Test clearing of cache"""
    cache = key_cache
    cache.set("test", {"kid": "test"})
    cache.clear()

    result = cache.get("test")
    assert result is None


@pytest.mark.asyncio
async def test_schema_service_get_tables(mocker, app):
    """Test getting all tables"""
    mock_tables = ["users", "profiles", "tasks"]

    mocker.patch(
        "services.supabase_client.supabase_client.rpc",
        return_value={"data": mock_tables}
    )

    tables = await SchemaService.get_all_tables()

    assert len(tables) == 3
    assert "users" in tables
    assert "profiles" in tables
    assert "tasks" in tables


@pytest.mark.asyncio
async def test_schema_service_discover(mocker, app):
    """Test full schema discovery"""
    from datetime import datetime

    mock_tables = ["users", "profiles", "tasks"]

    mocker.patch(
        "services.schema_service.SchemaService.get_all_tables",
        return_value=mock_tables
    )

    result = await SchemaService.discover_schema()

    assert len(result.tables) == 3
    assert "timestamp" in result
    assert result.timestamp is not None
