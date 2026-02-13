"""
Quick test to verify JWT validation directly
"""
import asyncio
import httpx
from jose import jwt, jwk

SUPABASE_URL = "https://icakwywcpldldvcyhpqe.supabase.co"


async def test_jwks():
    """Test fetching and using JWKS"""
    # Fetch JWKS
    url = f"{SUPABASE_URL}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        jwks = response.json()

    print(f"JWKS keys: {len(jwks.get('keys', []))}")
    for key in jwks.get("keys", []):
        print(f"  - kid: {key.get('kid')}, alg: {key.get('alg')}")

    # Test token from the login response
    test_token = input("\nPaste the access_token from login: ").strip()

    # Decode header
    header = jwt.get_unverified_header(test_token)
    print(f"\nToken header: {header}")

    # Find matching key
    kid = header.get("kid")
    alg = header.get("alg", "ES256")

    matching_key = None
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            matching_key = key_data
            break

    if not matching_key:
        print(f"ERROR: Key {kid} not found in JWKS!")
        return

    print(f"\nFound matching key: {matching_key.get('kid')}")

    # Construct public key and validate
    try:
        public_key = jwk.construct(matching_key, alg)
        print(f"Public key constructed successfully")

        # Decode and verify
        payload = jwt.decode(test_token, public_key, algorithms=[alg])
        print(f"\nToken validated successfully!")
        print(f"Payload: {payload}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_jwks())
