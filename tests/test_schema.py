"""
Schema discovery tests
"""
import pytest
from models.schema import TableInfo, TableSchema, SchemaDiscoveryResponse


@pytest.mark.asyncio
async def test_get_schemas_unauthenticated(client, app, mocker):
    """Test schema discovery endpoint"""
    mocker.patch(
        "services.schema_service.SchemaService.discover_schema",
        return_value=SchemaDiscoveryResponse(
            tables=["users", "profiles", "tasks"],
            timestamp="2025-01-01T00:00:00"
        )
    )

    response = await client.get("/api/admin/schemas")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "tables" in data
    assert len(data["tables"]) == 3
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_get_schemas_with_token(client, app, mocker):
    """Test schema discovery with authentication"""
    mocker.patch(
        "services.schema_service.SchemaService.discover_schema",
        return_value=SchemaDiscoveryResponse(
            tables=["users", "profiles"],
            timestamp="2025-01-01T00:00:00"
        )
    )

    response = await client.get(
        "/api/admin/schemas",
        cookies={"supabase-auth-token": "test-token"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "tables" in data


@pytest.mark.asyncio
async def test_table_info_model():
    """Test TableInfo model"""
    table = TableInfo(table_name="users", row_count=100)
    assert table.table_name == "users"
    assert table.row_count == 100

    # Test without row count
    table = TableInfo(table_name="profiles")
    assert table.table_name == "profiles"
    assert table.row_count is None


@pytest.mark.asyncio
async def test_table_schema_model():
    """Test TableSchema model"""
    columns = [
        {"column_name": "id", "data_type": "integer", "is_nullable": False},
        {"column_name": "email", "data_type": "text", "is_nullable": True}
    ]
    schema = TableSchema(table_name="users", columns=columns)

    assert schema.table_name == "users"
    assert len(schema.columns) == 2
    assert schema.columns[0]["column_name"] == "id"


@pytest.mark.asyncio
async def test_schema_discovery_response_model():
    """Test SchemaDiscoveryResponse model"""
    response = SchemaDiscoveryResponse(
        tables=["users", "profiles"],
        timestamp="2025-01-01T00:00:00"
    )

    assert len(response.tables) == 2
    assert response.timestamp == "2025-01-01T00:00:00"
