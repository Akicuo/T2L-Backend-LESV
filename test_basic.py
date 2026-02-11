"""
Basic tests for the Python FastAPI backend
Run without Supabase connection to validate models and structure
"""
import os
import sys

# Set test environment variables before importing main
os.environ.update({
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_KEY": "test-key",
    "ENVIRONMENT": "development",
    "CORS_ORIGINS": "http://localhost:5173",
})

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        import httpx
        from fastapi import FastAPI
        from pydantic import BaseModel
        print("  [OK] Basic imports successful")
    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False
    return True

def test_models():
    """Test Pydantic models"""
    print("\nTesting models...")
    from main import LoginRequest, LoginResponse, TokenValidationResponse

    # Test LoginRequest
    try:
        login_req = LoginRequest(email="test@example.com", password="password123")
        print(f"  [OK] LoginRequest: {login_req.email}")
    except Exception as e:
        print(f"  [FAIL] LoginRequest error: {e}")
        return False

    # Test LoginResponse
    try:
        login_resp = LoginResponse(
            access_token="test_token",
            user_id="user-123",
            email="test@example.com",
            role="authenticated"
        )
        print(f"  [OK] LoginResponse: {login_resp.email}")
    except Exception as e:
        print(f"  [FAIL] LoginResponse error: {e}")
        return False

    # Test TokenValidationResponse
    try:
        valid_resp = TokenValidationResponse(
            valid=True,
            user_id="user-123",
            email="test@example.com",
            role="authenticated"
        )
        print(f"  [OK] TokenValidationResponse: valid={valid_resp.valid}")
    except Exception as e:
        print(f"  [FAIL] TokenValidationResponse error: {e}")
        return False

    return True

def test_services():
    """Test service classes structure"""
    print("\nTesting service classes...")
    from main import JwtService, SupabaseAuthService, JwksKeyCache, key_cache

    # Test key cache
    try:
        key_cache.set("test-kid", {"kty": "EC", "crv": "P-256"})
        cached = key_cache.get("test-kid")
        assert cached is not None
        print("  [OK] JwksKeyCache working")
    except Exception as e:
        print(f"  [FAIL] JwksKeyCache error: {e}")
        return False

    # Verify service classes have required methods
    jwt_methods = dir(JwtService)
    assert "validate_token" in jwt_methods
    assert "fetch_jwks" in jwt_methods
    print("  [OK] JwtService has required methods")

    auth_methods = dir(SupabaseAuthService)
    assert "login" in auth_methods
    assert "get_user" in auth_methods
    assert "logout" in auth_methods
    print("  [OK] SupabaseAuthService has required methods")

    return True

def test_app_creation():
    """Test FastAPI app creation"""
    print("\nTesting FastAPI app creation...")
    from main import app

    # Check app exists
    assert hasattr(app, 'routes')
    print(f"  [OK] FastAPI app created with {len(app.routes)} routes")

    # List all routes
    route_names = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            for method in route.methods:
                route_names.append(f"{method} {route.path}")

    print("  Routes:")
    for name in sorted(route_names):
        print(f"    {name}")

    return True

def main():
    print("=" * 50)
    print("Time2Log Python Backend - Basic Tests")
    print("=" * 50)

    tests = [
        ("Imports", test_imports),
        ("Models", test_models),
        ("Services", test_services),
        ("App Creation", test_app_creation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n[FAIL] {name} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
