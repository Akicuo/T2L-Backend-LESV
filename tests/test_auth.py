"""
Authentication endpoint tests
"""
import pytest
from unittest.mock import patch
from fastapi import status

from models.auth import LoginRequest, TokenValidationResponse


@pytest.mark.asyncio
async def test_health_endpoint(client, app):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_test_endpoint(client, app):
    """Test test endpoint"""
    response = await client.get("/api/test")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_login_success(client, app, mocker):
    """Test successful login"""
    mock_auth_response = {
        "access_token": "test-token-abc123",
        "user": {
            "id": "user-123",
            "email": "test@example.com"
        }
    }

    async def mock_login(*args, **kwargs):
        return mock_auth_response

    async def mock_get_user(*args, **kwargs):
        return {
            "id": "user-123",
            "email": "test@example.com",
            "user_metadata": {"person_name": "Test User"},
            "app_metadata": {"role": "authenticated"}
        }

    mocker.patch("services.auth_service.AuthService.login", side_effect=mock_login)
    mocker.patch("services.auth_service.AuthService.get_user", side_effect=mock_get_user)

    response = await client.post(
        "/api/login",
        json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, app, mocker):
    """Test login with invalid credentials"""
    async def mock_login(*args, **kwargs):
        raise Exception("Invalid credentials")

    mocker.patch("services.auth_service.AuthService.login", side_effect=mock_login)

    response = await client.post(
        "/api/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_token_valid(client, app, mocker):
    """Test token validation with valid token"""
    from models.user import TokenMetadata

    async def mock_validate(*args, **kwargs):
        return TokenMetadata(
            user_id="user-123",
            email="test@example.com",
            role="authenticated",
            person_name="Test User"
        )

    mocker.patch("services.jwt_service.JwtService.validate_token", side_effect=mock_validate)

    response = await client.get(
        "/api/verify-token",
        cookies={"supabase-auth-token": "test-token-abc123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_verify_token_no_token(client, app, mocker):
    """Test token validation without token"""
    async def mock_validate(*args, **kwargs):
        return None

    mocker.patch("services.jwt_service.JwtService.validate_token", side_effect=mock_validate)

    response = await client.get("/api/verify-token")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


@pytest.mark.asyncio
async def test_logout(client, app):
    """Test logout endpoint"""
    response = await client.post("/api/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_legacy_auth_validation_valid(client, app, mocker):
    """Test legacy auth validation endpoint"""
    from models.user import TokenMetadata

    async def mock_validate(*args, **kwargs):
        return TokenMetadata(
            user_id="user-123",
            email="test@example.com",
            role="authenticated"
        )

    mocker.patch("services.jwt_service.JwtService.validate_token", side_effect=mock_validate)

    response = await client.post(
        "/api/auth/validate",
        headers={"Authorization": "Bearer test-token-abc123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


@pytest.mark.asyncio
async def test_legacy_auth_validation_missing_header(client, app):
    """Test legacy auth validation without header"""
    response = await client.post("/api/auth/validate")

    assert response.status_code == 401
