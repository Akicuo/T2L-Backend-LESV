"""
Database schema-related models
"""
from typing import Optional

from pydantic import BaseModel


class TableInfo(BaseModel):
    """Information about a database table"""
    table_name: str
    row_count: Optional[int] = None


class TableSchema(BaseModel):
    """Schema information for a table"""
    table_name: str
    columns: list[dict]


class SchemaDiscoveryResponse(BaseModel):
    """Response from schema discovery endpoint"""
    tables: list[str]
    timestamp: str
