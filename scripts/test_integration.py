"""
Quick integration test using actual server and credentials

This tests the actual running server with real Supabase credentials.
Update EMAIL and PASSWORD below with your actual values.
"""
import asyncio
import os

import httpx

# Configuration - UPDATE THESE WITH YOUR ACTUAL CREDENTIALS
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
EMAIL = "test_bob@gmail.com"
PASSWORD = "SumanAllegro10"


async def test_health_check():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")


async def test_login():
    """Test login with credentials"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        print(f"✅ Login attempt: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login successful!")
            print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"   User ID: {data.get('user_id', 'N/A')}")
            print(f"   Email: {data.get('email', 'N/A')}")
        else:
            print(f"   ❌ Login failed!")
            print(f"   Error: {response.text}")


async def test_get_tables(token: str):
    """Test schema discovery"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/admin/schemas",
            cookies={"supabase-auth-token": token}
        )
        print(f"✅ Schema discovery: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   Tables found: {len(data.get('tables', []))}")
            for table in data.get('tables', [])[:5]:
                print(f"     - {table}")
        else:
            print(f"   Error: {response.text}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print(" T2L Backend Integration Test")
    print("=" * 60)
    print(f"\nServer: {BASE_URL}")
    print(f"Email: {EMAIL}")
    print(f"Password: {'*' * len(PASSWORD)}")
    print()

    # First, test health
    print("\n1. Testing health endpoint...")
    await test_health_check()

    # Test login
    print("\n2. Testing login...")
    await test_login()

    # Get token for next tests
    token = None
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")

    # Test schema discovery with token
    if token:
        print("\n3. Testing schema discovery...")
        await test_get_tables(token)

    print("\n" + "=" * 60)
    print(" Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
