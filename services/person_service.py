"""
Person service for fetching person data from the database
"""
import logging
from typing import Optional
from dataclasses import dataclass

from services.supabase_client import supabase_client

logger = logging.getLogger(__name__)


@dataclass
class PersonData:
    """Person data from the database"""
    person_id: Optional[str] = None
    person_name: Optional[str] = None


class PersonService:
    """Service for fetching person data from app.profiles table"""

    @staticmethod
    async def get_person_by_user_id(user_id: str, token: Optional[str] = None) -> PersonData:
        """
        Look up person data from app.profiles table by user_id (id column).

        Args:
            user_id: The Supabase auth user ID
            token: Optional auth token for RLS passthrough

        Returns:
            PersonData with person_id and person_name if found, empty otherwise
        """
        try:
            result = await supabase_client.table_select(
                table="profiles",
                columns="id, first_name, last_name",
                filters={"id": user_id},
                limit=1,
                schema="app",
                token=token,
            )

            # table_select returns a list
            if result and len(result) > 0:
                profile = result[0]
                first_name = profile.get("first_name", "")
                last_name = profile.get("last_name", "")
                # Combine first and last name
                full_name = f"{first_name} {last_name}".strip()

                return PersonData(
                    person_id=profile.get("id"),
                    person_name=full_name if full_name else None,
                )

            logger.info(f"No profile found for user_id: {user_id}")
            return PersonData()

        except Exception as e:
            logger.warning(f"Failed to fetch profile data for user {user_id}: {e}")
            return PersonData()

    @staticmethod
    async def get_person_name(user_id: str, token: Optional[str] = None, fallback: Optional[str] = None) -> Optional[str]:
        """
        Get person name by user_id with optional fallback.

        Args:
            user_id: The Supabase auth user ID
            token: Optional auth token for RLS passthrough
            fallback: Fallback value if person not found

        Returns:
            Person name or fallback value
        """
        person = await PersonService.get_person_by_user_id(user_id, token)
        if person.person_name:
            return person.person_name
        return fallback
