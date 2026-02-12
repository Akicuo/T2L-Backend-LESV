"""
Authentication service using lightweight Supabase client
"""
import logging
from typing import Any

from fastapi import HTTPException

from services.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication operations using lightweight Supabase client"""

    @staticmethod
    async def login(email: str, password: str) -> dict[str, Any]:
        """Login with email and password"""
        try:
            result = await supabase_client.sign_in_with_password(email, password)
            return result
        except Exception as e:
            logger.error(f"Login failed for {email}: {e}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

    @staticmethod
    async def get_user(token: str) -> dict[str, Any]:
        """Get user information from token"""
        try:
            user_data = await supabase_client.get_user(token)
            return user_data
        except Exception as e:
            logger.error(f"Get user failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    async def logout(token: str) -> None:
        """Logout and invalidate token"""
        try:
            await supabase_client.sign_out(token)
        except Exception as e:
            logger.warning(f"Logout failed (non-critical): {e}")
