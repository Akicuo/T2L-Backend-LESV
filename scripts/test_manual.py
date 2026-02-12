"""
Manual testing script for T2L-Backend-LESV

This script provides interactive testing of all API endpoints.
"""
import asyncio
import json
from datetime import datetime

import httpx

# Configuration
BASE_URL = "http://localhost:8080"
EMAIL = "test@example.com"  # Replace with actual test email
PASSWORD = "testpassword"    # Replace with actual test password


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def print_result(name: str, response: httpx.Response, show_data: bool = True):
    """Print formatted result"""
    status_color = "\033[92m" if response.status_code < 400 else "\033[91m"  # Green or Red
    reset = "\033[0m"

    print(f"\n{name}:")
    print(f"  Status: {status_color}{response.status_code}{reset}")
    print(f"  URL: {response.request.url}")

    if show_data and response.status_code < 400:
        try:
            data = response.json()
            print(f"  Data: {json.dumps(data, indent=4)}")
        except Exception:
            print(f"  Data: {response.text[:200]}")
    elif response.status_code >= 400:
        print(f"  Error: {response.text[:200]}")


async def test_health_endpoints():
    """Test health check endpoints"""
    print_section("HEALTH CHECK ENDPOINTS")

    async with httpx.AsyncClient() as client:
        # Test /health
        response = await client.get(f"{BASE_URL}/health")
        print_result("GET /health", response)

        # Test /api/test
        response = await client.get(f"{BASE_URL}/api/test")
        print_result("GET /api/test", response)


async def test_auth_endpoints():
    """Test authentication endpoints"""
    print_section("AUTHENTICATION ENDPOINTS")

    async with httpx.AsyncClient() as client:
        # Test login with valid credentials
        print("\n1. Testing login with valid credentials...")
        response = await client.post(
            f"{BASE_URL}/api/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        print_result("POST /api/login (valid)", response)

        # Store token if login successful
        token = None
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"\n  Token received: {token[:50]}..." if token else "  No token received")
        else:
            print("\n  Login failed - skipping auth tests")
            return

        # Test login with invalid credentials
        print("\n2. Testing login with invalid credentials...")
        response = await client.post(
            f"{BASE_URL}/api/login",
            json={"email": "invalid@example.com", "password": "wrongpassword"}
        )
        print_result("POST /api/login (invalid)", response)

        # Test verify-token with valid token
        print("\n3. Testing token validation...")
        response = await client.get(
            f"{BASE_URL}/api/verify-token",
            cookies={"supabase-auth-token": token}
        )
        print_result("GET /api/verify-token (valid)", response)

        # Test verify-token without token
        print("\n4. Testing token validation without token...")
        response = await client.get(f"{BASE_URL}/api/verify-token")
        print_result("GET /api/verify-token (no token)", response)

        # Test logout
        print("\n5. Testing logout...")
        response = await client.post(f"{BASE_URL}/api/logout")
        print_result("POST /api/logout", response)

        # Test legacy auth validation
        print("\n6. Testing legacy auth validation endpoint...")
        response = await client.post(
            f"{BASE_URL}/api/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )
        print_result("POST /api/auth/validate", response)


async def test_admin_endpoints(token: str | None):
    """Test admin endpoints"""
    print_section("ADMIN ENDPOINTS")

    if not token:
        print("\nNo token provided - skipping admin tests")
        return

    async with httpx.AsyncClient() as client:
        # Test schema discovery
        print("\n1. Testing schema discovery...")
        response = await client.get(
            f"{BASE_URL}/api/admin/schemas",
            cookies={"supabase-auth-token": token}
        )
        print_result("GET /api/admin/schemas", response)


async def main():
    """Run all tests"""
    print_section("T2L Backend Manual Test Suite")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        await test_health_endpoints()
        await test_auth_endpoints()

        # Get a fresh token for admin tests
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/login",
                json={"email": EMAIL, "password": PASSWORD}
            )
            token = None
            if response.status_code == 200:
                token = response.json().get("access_token")

        await test_admin_endpoints(token)

        print_section("TESTS COMPLETED")
        print("\nAll tests finished. Review results above.")

    except Exception as e:
        print(f"\n\033[91mERROR: {e}\033[0m")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" T2L Backend Manual Test Script")
    print("=" * 60)
    print("\nIMPORTANT: Update EMAIL and PASSWORD in this script before running!")
    print(f"Current email: {EMAIL}")
    print(f"Current password: {'*' * len(PASSWORD)}")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    input()

    asyncio.run(main())
