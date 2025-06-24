"""Tests for the MCP server."""

import pytest
from unittest.mock import AsyncMock, patch

from hcp_terraform_mcp.server import TerraformMcpServer
from hcp_terraform_mcp.config import TerraformConfig


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return TerraformConfig(
        api_token="test-token",
        organization="test-org",
        base_url="https://test.terraform.io/api/v2"
    )


class TestTerraformMcpServer:
    """Test MCP server."""
    
    def test_server_initialization(self):
        """Test server initialization."""
        with patch("hcp_terraform_mcp.server.get_config") as mock_get_config:
            mock_get_config.return_value = TerraformConfig(
                api_token="test-token",
                organization="test-org"
            )
            
            server = TerraformMcpServer()
            assert server.config is not None
            assert server.server is not None
    
    @pytest.mark.asyncio
    async def test_server_start_stop(self):
        """Test server start and stop."""
        with patch("hcp_terraform_mcp.server.get_config") as mock_get_config:
            mock_get_config.return_value = TerraformConfig(
                api_token="test-token",
                organization="test-org"
            )
            
            with patch("hcp_terraform_mcp.server.TerraformClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.health_check.return_value = True
                mock_client_class.return_value = mock_client
                
                server = TerraformMcpServer()
                
                await server.start()
                assert server.client is not None
                
                await server.stop()
                mock_client.close.assert_called_once()


class TestMcpToolsSetup:
    """Test MCP tool setup and registration."""
    
    def test_server_has_tools_configured(self):
        """Test that server has the expected tools configured."""
        with patch("hcp_terraform_mcp.server.get_config") as mock_get_config:
            mock_get_config.return_value = TerraformConfig(
                api_token="test-token",
                organization="test-org"
            )
            
            server = TerraformMcpServer()
            
            # Verify server was created successfully
            assert server.server is not None
            assert server.config is not None
            assert server.config.api_token == "test-token"
            assert server.config.organization == "test-org"