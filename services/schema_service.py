"""
Database schema discovery service
"""
import logging
from datetime import datetime

from services.supabase_client import supabase_client
from models.schema import TableInfo, SchemaDiscoveryResponse

logger = logging.getLogger(__name__)


class SchemaService:
    """Database schema discovery using Supabase RPC"""

    @staticmethod
    async def get_all_tables() -> list[str]:
        """Get all tables in the public schema using RPC"""
        try:
            result = await supabase_client.rpc("get_tables")
            return result.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []

    @staticmethod
    async def get_table_columns(table_name: str) -> list[dict]:
        """Get column information for a specific table"""
        try:
            # Query information_schema.columns via direct table access
            result = await supabase_client.rpc(
                "get_table_columns",
                params={"table_name": table_name}
            )
            return result.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get columns for {table_name}: {e}")
            return []

    @staticmethod
    async def get_table_count(table_name: str) -> int:
        """Get row count for a specific table"""
        try:
            result = await supabase_client.table_select(
                table_name,
                columns="*",
                limit=1
            )
            # Extract count from content-range header if available
            return len(result.get("data", []))
        except Exception as e:
            logger.warning(f"Could not get count for {table_name}: {e}")
            return 0

    @staticmethod
    async def discover_schema() -> SchemaDiscoveryResponse:
        """Perform full schema discovery"""
        logger.info("Starting schema discovery")
        tables = await SchemaService.get_all_tables()

        return SchemaDiscoveryResponse(
            tables=tables,
            timestamp=datetime.now().isoformat()
        )
