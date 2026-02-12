"""
User-related models
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenMetadata:
    """Extracted JWT token metadata"""
    user_id: str
    email: str
    role: str = "authenticated"
    person_id: Optional[str] = None
    person_name: Optional[str] = None
