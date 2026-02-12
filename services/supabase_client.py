"""
Lightweight Supabase HTTP Client

This module provides a minimal HTTP-based client for Supabase operations
without the heavy dependencies of the official supabase package.
"""
import logging
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Lightweight HTTP client for Supabase operations"""

    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.auth_url = f"{url}/auth/v1"
        self.rest_url = f"{url}/rest/v1"

    def _get_headers(self, use_auth: bool = False, token: Optional[str] = None) -> dict[str, str]:
        """Build headers for API requests"""
        headers = {
            "apikey": self.key,
            "Content-Type": "application/json",
        }

        if use_auth and token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with error handling"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, **kwargs)

            if response.status_code >= 400:
                logger.error(f"Supabase API error: {response.status_code} - {response.text}")

            return response

    # ===================
    # Auth Operations
    # ===================

    async def sign_in_with_password(self, email: str, password: str) -> dict[str, Any]:
        """Sign in with email and password"""
        url = f"{self.auth_url}/token?grant_type=password"
        payload = {"email": email, "password": password}

        response = await self._request(
            "POST",
            url,
            json=payload,
            headers=self._get_headers()
        )

        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")

        return response.json()

    async def get_user(self, token: str) -> dict[str, Any]:
        """Get user information from token"""
        url = f"{self.auth_url}/user"

        response = await self._request(
            "GET",
            url,
            headers=self._get_headers(use_auth=True, token=token)
        )

        if response.status_code != 200:
            raise Exception(f"Get user failed: {response.text}")

        return response.json()

    async def sign_out(self, token: str) -> None:
        """Sign out user (invalidates token)"""
        url = f"{self.auth_url}/logout"

        await self._request(
            "POST",
            url,
            headers=self._get_headers(use_auth=True, token=token)
        )

    # ===================
    # Database Operations
    # ===================

    async def table_select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> dict[str, Any]:
        """Select rows from a table"""
        url = f"{self.rest_url}/{table}"
        params = {"select": columns}

        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"

        if limit:
            params["limit"] = str(limit)

        response = await self._request(
            "GET",
            url,
            params=params,
            headers=self._get_headers()
        )

        if response.status_code not in (200, 406):
            raise Exception(f"Table select failed: {response.text}")

        return response.json()

    async def table_insert(self, table: str, data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
        """Insert row(s) into a table"""
        url = f"{self.rest_url}/{table}"

        response = await self._request(
            "POST",
            url,
            json=data,
            headers=self._get_headers()
        )

        if response.status_code not in (200, 201):
            raise Exception(f"Table insert failed: {response.text}")

        return response.json()

    async def table_update(
        self,
        table: str,
        data: dict[str, Any],
        filters: dict[str, Any]
    ) -> dict[str, Any]:
        """Update rows in a table"""
        url = f"{self.rest_url}/{table}"
        params = {}

        for key, value in filters.items():
            params[key] = f"eq.{value}"

        response = await self._request(
            "PATCH",
            url,
            json=data,
            params=params,
            headers=self._get_headers()
        )

        if response.status_code != 200:
            raise Exception(f"Table update failed: {response.text}")

        return response.json()

    async def table_delete(self, table: str, filters: dict[str, Any]) -> None:
        """Delete rows from a table"""
        url = f"{self.rest_url}/{table}"
        params = {}

        for key, value in filters.items():
            params[key] = f"eq.{value}"

        response = await self._request(
            "DELETE",
            url,
            params=params,
            headers=self._get_headers()
        )

        if response.status_code != 204:
            raise Exception(f"Table delete failed: {response.text}")

    async def rpc(self, function_name: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Call a Postgres function via RPC"""
        url = f"{self.rest_url}/rpc/{function_name}"

        response = await self._request(
            "POST",
            url,
            json=params or {},
            headers=self._get_headers()
        )

        if response.status_code not in (200, 406):
            raise Exception(f"RPC call failed: {response.text}")

        return response.json()


# Global Supabase client instance
supabase_client = SupabaseClient(settings.SUPABASE_URL, settings.SUPABASE_KEY)
