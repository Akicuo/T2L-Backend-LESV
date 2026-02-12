"""
Real integration test for T2L Backend

This script tests the ACTUAL running server with YOUR REAL Supabase credentials.
It verifies that endpoints are working correctly with your Supabase instance.
"""
import asyncio
import os
import sys

import httpx

# Import from actual server configuration
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
EMAIL = os.getenv("TEST_EMAIL", "test_bob@gmail.com")  # User's actual email
PASSWORD = os.getenv("TEST_PASSWORD", "SumanAllegro10")  # User's actual password


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"  # ✅
    RED = "\033[91m"    # ❌
    YELLOW = "\033[93m"  # ⚠️
    BLUE = "\033[94m"    # ℹ️
    RESET = "\033[0m"     # Reset


def print_header(message: str):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{'=' * 60}")
    print(f"{message:^60}")
    print("=" * 60)


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}")


async def test_health_check():
    """Test health check endpoint"""
    print_header("1. HEALTH CHECK")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/health", timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                print_success(f"Health check passed: {data.get('status', 'N/A')}")
                print_info(f"Response: {data}")
            else:
                print_error(f"Health check failed: {response.status_code}")
                print_warning(f"Response: {response.text[:100]}")

    except Exception as e:
        print_error(f"Health check error: {e}")


async def test_login():
    """Test login with REAL Supabase credentials"""
    print_header("2. LOGIN TEST")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/login",
                json={"email": EMAIL, "password": PASSWORD},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                print_success(f"Login successful!")
                print_info(f"Access token: {data.get('access_token', 'N/A')[:30]}...")

                # Verify user data endpoint
                token = data.get("access_token")
                if token:
                    user_response = await client.get(
                        f"{BASE_URL}/api/verify-token",
                        cookies={"supabase-auth-token": token},
                        timeout=10.0
                    )

                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        print_success("Token validation passed!")
                    else:
                        print_warning(f"Token validation returned: {user_response.status_code}")

            elif response.status_code == 401:
                print_error("Login failed - Invalid credentials")
                print_info("This is expected if the user doesn't exist in your Supabase")

            else:
                print_error(f"Login failed with status: {response.status_code}")
                print_warning(f"Response: {response.text[:200]}")

    except Exception as e:
        print_error(f"Login error: {e}")


async def test_verify_endpoint():
    """Test verify token endpoint (should work without token)"""
    print_header("3. VERIFY ENDPOINT (NO TOKEN)")

    try:
        async with httpx.AsyncClient() as client:
            # Test without token
            response = await client.get(f"{BASE_URL}/api/verify-token", timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                if data.get("valid") is False:
                    print_success("Token validation correctly returns false for no token")
                else:
                    print_warning(f"Token validation unexpected: {data}")
            else:
                print_error(f"Verify endpoint failed: {response.status_code}")

    except Exception as e:
        print_error(f"Verify endpoint error: {e}")


async def test_logout():
    """Test logout endpoint"""
    print_header("4. LOGOUT TEST")

    # First login to get a token
    token = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/login",
                json={"email": EMAIL, "password": PASSWORD},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print_info(f"Got token: {token[:20]}...")

                # Now test logout
                logout_response = await client.post(
                    f"{BASE_URL}/api/logout",
                    cookies={"supabase-auth-token": token},
                    timeout=10.0
                )

                if logout_response.status_code == 200:
                    print_success("Logout successful!")
                else:
                    print_warning(f"Logout returned: {logout_response.status_code}")

    except Exception as e:
        print_error(f"Logout error: {e}")


async def test_schema_discovery():
    """Test schema discovery endpoint"""
    print_header("5. SCHEMA DISCOVERY")

    # First login to get token
    token = None
    try:
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                f"{BASE_URL}/api/login",
                json={"email": EMAIL, "password": PASSWORD},
                timeout=10.0
            )

            if login_response.status_code == 200:
                data = login_response.json()
                token = data.get("access_token")
                print_info(f"Got token: {token[:20]}...")

                # Test schema discovery
                response = await client.get(
                    f"{BASE_URL}/api/admin/schemas",
                    cookies={"supabase-auth-token": token},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    tables = data.get("tables", [])

                    if tables and len(tables) > 0:
                        print_success(f"Found {len(tables)} tables")
                        for i, table in enumerate(tables[:5], 1):
                            print_info(f"  {i+1}. {table}")
                        if len(tables) > 5:
                            print_info(f"  ... and {len(tables) - 5} more")
                    else:
                        print_warning("No tables found or empty response")
                else:
                    print_error(f"Schema discovery failed: {response.status_code}")
                    print_warning(f"Response: {response.text[:200]}")

            elif login_response.status_code == 401:
                print_error("Login failed - Invalid credentials")
                print_info("Verify user exists in Supabase and password is correct")
                print_info(f"  Email: {EMAIL}")
                print_info(f"  Password: {'*' * len(PASSWORD)}")

    except Exception as e:
        print_error(f"Schema discovery error: {e}")


async def run_all_tests():
    """Run all integration tests"""
    print(f"\n{Colors.BLUE}╔{'═' * 58}╗")
    print(f"{Colors.BLUE}  T2L Backend Real Integration Test ")
    print(f"{Colors.BLUE}╚{'═' * 58}╝")
    print()

    print_info("This will test your ACTUAL Supabase backend")
    print_info(f"  Server: {BASE_URL}")
    print_info(f"  Email: {EMAIL}")
    print_info(f"  Password: {'*' * len(PASSWORD)}")
    print()
    print_warning("Make sure:")
    print_warning("  1. Server is running (python main.py)")
    print_warning("  2. .env file is configured with your credentials")
    print_warning("  3. User exists in your Supabase project")
    print()

    # Run tests
    await test_health_check()
    print()
    await test_verify_endpoint()
    print()
    await test_login()
    print()
    await test_schema_discovery()
    print()
    await test_logout()
    print()

    print(f"\n{Colors.BLUE}{'═' * 58}═")
    print(f"{Colors.GREEN}All tests completed!{Colors.RESET}")
    print()
    print("Review the results above.")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print()
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(1)
