"""Tests for the MCP server."""

from unittest.mock import AsyncMock, patch

import pytest

from hcp_terraform_mcp.config import TerraformConfig
from hcp_terraform_mcp import server as hcp_server


@pytest.fixture
def mock_config():
    """Mock configuration."""
    with patch("hcp_terraform_mcp.server.get_config") as mock_get_config:
        config = TerraformConfig(
            api_token="test-token",
            organization="test-org",
            base_url="https://test.terraform.io/api/v2",
            debug_mode=True,
        )
        mock_get_config.return_value = config
        yield config


@pytest.fixture
def mock_client():
    """Mock TerraformClient."""
    with patch("hcp_terraform_mcp.server.TerraformClient") as mock:
        client = AsyncMock()
        client.health_check.return_value = True
        mock.return_value = client
        yield client


@pytest.fixture
def mock_tool_handlers():
    """Mock ToolHandlers."""
    with patch(
        "hcp_terraform_mcp.server.tool_handlers", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.fixture
def mock_resource_handler():
    """Mock ResourceHandler."""
    with patch(
        "hcp_terraform_mcp.server.resource_handler", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.mark.asyncio
async def test_server_start_stop(mock_config, mock_client):
    """Test server start and stop."""
    await hcp_server.start_server()
    assert hcp_server.client is not None
    assert hcp_server.tool_handlers is not None
    assert hcp_server.resource_handler is not None
    mock_client.health_check.assert_called_once()

    await hcp_server.stop_server()
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_list_tools(mock_config):
    """Test that list_tools returns the correct tools."""
    tools = await hcp_server.list_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert tools[0].name == "health_check"


@pytest.mark.asyncio
async def test_call_tool_dispatch(mock_config, mock_tool_handlers):
    """Test that call_tool dispatches to the correct handler."""
    await hcp_server.call_tool(name="health_check", arguments={})
    mock_tool_handlers.dispatch.assert_called_once_with("health_check", {})


@pytest.mark.asyncio
async def test_list_resources(mock_config, mock_resource_handler):
    """Test that list_resources returns a list of resources."""
    await hcp_server.list_resources()
    mock_resource_handler.list_resources.assert_called_once()


@pytest.mark.asyncio
async def test_read_resource(mock_config, mock_resource_handler):
    """Test that read_resource calls the resource handler."""
    await hcp_server.read_resource(uri="terraform://organization/info")
    mock_resource_handler.read_resource.assert_called_once_with(
        "terraform://organization/info"
    )
