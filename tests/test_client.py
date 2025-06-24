"""Tests for the Terraform API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tfc_mcp.client import TerraformClient, TerraformApiError, RateLimiter
from tfc_mcp.config import TerraformConfig
from tfc_mcp.models import JsonApiResponse, JsonApiResource


@pytest.fixture
def config():
    """Test configuration."""
    return TerraformConfig(
        api_token="test-token",
        organization="test-org",
        base_url="https://test.terraform.io/api/v2"
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    with patch("tfc_mcp.client.httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


class TestRateLimiter:
    """Test rate limiter."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Should allow first two requests immediately
        await limiter.acquire()
        await limiter.acquire()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excess_requests(self):
        """Test that rate limiter blocks requests exceeding limit."""
        limiter = RateLimiter(max_requests=1, window_seconds=0.05)
        
        # First request should be immediate
        await limiter.acquire()
        
        # Second request should be delayed
        import time
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time
        
        # Should have waited at least some time but not too long
        assert 0.03 < elapsed < 0.2


class TestTerraformClient:
    """Test Terraform API client."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, config):
        """Test client initialization."""
        client = TerraformClient(config)
        assert client.config == config
        assert client.rate_limiter is not None
    
    @pytest.mark.asyncio
    async def test_successful_get_request(self, config, mock_httpx_client):
        """Test successful GET request."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "test-id",
                "type": "organizations",
                "attributes": {"name": "test-org"}
            }
        }
        mock_httpx_client.request.return_value = mock_response
        
        client = TerraformClient(config)
        response = await client.get("/test-endpoint")
        
        assert response.data is not None
        assert response.data.id == "test-id"
        assert response.data.type == "organizations"
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, config, mock_httpx_client):
        """Test API error handling."""
        # Setup mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errors": [
                {
                    "title": "Bad Request",
                    "detail": "Invalid parameter"
                }
            ]
        }
        mock_httpx_client.request.return_value = mock_response
        
        client = TerraformClient(config)
        
        with pytest.raises(TerraformApiError) as exc_info:
            await client.get("/test-endpoint")
        
        assert exc_info.value.status_code == 400
        assert "Bad Request" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, config, mock_httpx_client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "test-org",
                "type": "organizations"
            }
        }
        mock_httpx_client.request.return_value = mock_response
        
        client = TerraformClient(config)
        is_healthy = await client.health_check()
        
        assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, config, mock_httpx_client):
        """Test failed health check."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "errors": [{"title": "Unauthorized"}]
        }
        mock_httpx_client.request.return_value = mock_response
        
        client = TerraformClient(config)
        is_healthy = await client.health_check()
        
        assert is_healthy is False
    
    def test_organization_endpoint_generation(self, config):
        """Test organization endpoint generation."""
        client = TerraformClient(config)
        
        endpoint = client.get_organization_endpoint()
        assert endpoint == "/organizations/test-org"
        
        endpoint = client.get_organization_endpoint("projects")
        assert endpoint == "/organizations/test-org/projects"