"""
Endpoint Testing Script

Usage:
    python scripts/test_all_endpoints.py --user user@gmail.com --password "Password"
    python scripts/test_all_endpoints.py --user user@gmail.com --password "Password" --url http://localhost:8080
"""

import argparse
import asyncio
import json
from datetime import datetime

import httpx


class EndpointTester:
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.access_token = None
        self.results = []
        self.client: httpx.AsyncClient | None = None

    def print_header(self, title: str):
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def print_result(self, method: str, endpoint: str, status_code: int, response: dict | None, error: str | None = None):
        status_emoji = "OK" if status_code and 200 <= status_code < 300 else "FAIL"
        print(f"\n[{method}] {endpoint}")
        print(f"Status: {status_code} [{status_emoji}]")

        if error:
            print(f"Error: {error}")
        elif response is not None:
            # Pretty print JSON response
            try:
                formatted = json.dumps(response, indent=2, ensure_ascii=False)
                if len(formatted) > 500:
                    formatted = formatted[:500] + "\n... (truncated)"
                print(f"Response:\n{formatted}")
            except Exception:
                print(f"Response: {response}")

        self.results.append({
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "success": status_code and 200 <= status_code < 300,
        })

    async def request(self, method: str, endpoint: str, json_data: dict | None = None, headers: dict | None = None) -> tuple[int, dict | None, str | None]:
        url = f"{self.base_url}{endpoint}"
        try:
            merged_headers = headers or {}

            # Debug: print cookies being sent
            if self.client.cookies:
                print(f"  [DEBUG] Cookies being sent: {list(self.client.cookies.keys())}")
                for key, value in self.client.cookies.items():
                    print(f"  [DEBUG] Cookie '{key}': {value[:50]}...")

            response = await self.client.request(
                method=method,
                url=url,
                json=json_data,
                headers=merged_headers,
            )

            # Debug: print Set-Cookie headers from response
            set_cookie = response.headers.get("set-cookie")
            if set_cookie:
                print(f"  [DEBUG] Set-Cookie header: {set_cookie[:100]}...")

            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}

            return response.status_code, data, None
        except Exception as e:
            return None, None, str(e)

    async def run_tests(self):
        print(f"\nStarting endpoint tests at {datetime.now().isoformat()}")
        print(f"Base URL: {self.base_url}")
        print(f"User: {self.email}")

        # Use a single client instance to maintain cookies
        async with httpx.AsyncClient(timeout=30.0) as client:
            self.client = client

            # ============================================
            # PUBLIC ENDPOINTS (no authentication required)
            # ============================================
            self.print_header("PUBLIC ENDPOINTS")

            # 1. Health check
            status, data, error = await self.request("GET", "/health")
            self.print_result("GET", "/health", status, data, error)

            # 2. API Health check
            status, data, error = await self.request("GET", "/api/health")
            self.print_result("GET", "/api/health", status, data, error)

            # 3. Test endpoint
            status, data, error = await self.request("GET", "/test")
            self.print_result("GET", "/test", status, data, error)

            # ============================================
            # LOGIN
            # ============================================
            self.print_header("AUTHENTICATION")

            # 4. Login
            status, data, error = await self.request(
                "POST", "/api/login",
                json_data={"email": self.email, "password": self.password}
            )
            self.print_result("POST", "/api/login", status, data, error)

            if data and data.get("access_token"):
                self.access_token = data.get("access_token")
                print(f"\n>>> Logged in as: {data.get('email')}")
                print(f">>> User ID: {data.get('user_id')}")
                print(f">>> Role: {data.get('role')}")
                print(f">>> Cookies: {dict(client.cookies)}")

            # ============================================
            # PROTECTED ENDPOINTS (authentication required)
            # ============================================
            self.print_header("PROTECTED ENDPOINTS")

            # 5. Verify token
            status, data, error = await self.request("GET", "/api/verify-token")
            self.print_result("GET", "/api/verify-token", status, data, error)

            # 6. Admin schemas
            status, data, error = await self.request("GET", "/api/admin/schemas")
            self.print_result("GET", "/api/admin/schemas", status, data, error)

            # 7. Activities tags
            status, data, error = await self.request("GET", "/api/activities/tags")
            self.print_result("GET", "/api/activities/tags", status, data, error)

            # 8. Activities history
            status, data, error = await self.request("GET", "/api/activities/history")
            self.print_result("GET", "/api/activities/history", status, data, error)

            # 9. Create activity (POST)
            status, data, error = await self.request(
                "POST", "/api/activities/create",
                json_data={
                    "activity": {"id": "test-activity-id"},
                    "notes": "Test activity from endpoint tester",
                    "start_time": datetime.now().isoformat(),
                    "end_time": None,
                }
            )
            self.print_result("POST", "/api/activities/create", status, data, error)

            # 10. Auth validate (Bearer token)
            if self.access_token:
                status, data, error = await self.request(
                    "POST", "/api/auth/validate",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                self.print_result("POST", "/api/auth/validate", status, data, error)
            else:
                self.print_result("POST", "/api/auth/validate", None, None, "No access token available")

            # ============================================
            # LOGOUT (must be last!)
            # ============================================
            self.print_header("LOGOUT")

            # 11. Logout
            status, data, error = await self.request("POST", "/api/logout")
            self.print_result("POST", "/api/logout", status, data, error)

            # ============================================
            # VERIFY LOGOUT
            # ============================================
            self.print_header("VERIFY LOGOUT")

            # 12. Verify token should fail now
            status, data, error = await self.request("GET", "/api/verify-token")
            self.print_result("GET", "/api/verify-token (after logout)", status, data, error)

        # ============================================
        # SUMMARY
        # ============================================
        self.print_summary()

    def print_summary(self):
        self.print_header("SUMMARY")

        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful

        print(f"\nTotal tests: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        if failed > 0:
            print("\nFailed endpoints:")
            for r in self.results:
                if not r["success"]:
                    print(f"  - [{r['method']}] {r['endpoint']} (Status: {r['status_code']})")

        print("\n" + "=" * 60)
        print(f"Test completed at {datetime.now().isoformat()}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Test all API endpoints")
    parser.add_argument("--user", required=True, help="User email for login")
    parser.add_argument("--password", required=True, help="User password for login")
    parser.add_argument("--url", default="http://localhost:8080", help="Base URL of the API (default: http://localhost:8080)")

    args = parser.parse_args()

    tester = EndpointTester(
        base_url=args.url,
        email=args.user,
        password=args.password,
    )

    asyncio.run(tester.run_tests())


if __name__ == "__main__":
    main()
