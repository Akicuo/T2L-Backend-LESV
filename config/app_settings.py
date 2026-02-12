"""
Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional

# ================================
# Configuration
# ================================
class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    JWT_SECRET: Optional[str] = None
    COOKIE_NAME: str = "supabase-auth-token"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"
    PORT: int = 8080
    DISABLE_AUTH: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True