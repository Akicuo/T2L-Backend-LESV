"""
Admin routes
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from models.user import TokenMetadata
from models.schema import SchemaDiscoveryResponse
from services.schema_service import SchemaService
from services.jwt_service import JwtService
from utils.cookies import get_token_from_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/schemas", response_model=SchemaDiscoveryResponse)
async def get_schemas(
    token: str | None = Depends(get_token_from_cookie),
):
    """Discover all schemas and tables - for testing/admin purposes"""
    logger.info("Schema discovery endpoint called")

    # Optional: Require authentication for admin access
    # if token:
    #     metadata = await JwtService.validate_token(token)
    #     if not metadata or metadata.role != "admin":
    #         raise HTTPException(status_code=403, detail="Admin access required")

    result = await SchemaService.discover_schema()
    return result
