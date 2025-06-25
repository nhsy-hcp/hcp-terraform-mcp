"""Tests for the Terraform API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hcp_terraform_mcp.client import RateLimiter, TerraformApiError, TerraformClient
from hcp_terraform_mcp.config import TerraformConfig
from hcp_terraform_mcp.models import JsonApiResource, JsonApiResponse


@pytest.fixture
def config():
    """Test configuration."""
    return TerraformConfig(
        api_token="test-token",
        organization="test-org",
        base_url="https://test.terraform.io/api/v2",
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    with patch("hcp_terraform_mcp.client.httpx.AsyncClient") as mock:
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
                "attributes": {"name": "test-org"},
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
            "errors": [{"title": "Bad Request", "detail": "Invalid parameter"}]
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
            "data": {"id": "test-org", "type": "organizations"}
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
        mock_response.json.return_value = {"errors": [{"title": "Unauthorized"}]}
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


class TestProjectMethods:
    """Test project management methods."""

    @pytest.mark.asyncio
    async def test_create_project(self, config, mock_httpx_client):
        """Test project creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {
                "id": "prj-123",
                "type": "projects",
                "attributes": {
                    "name": "test-project",
                    "description": "Test description",
                },
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.create_project("test-project", "Test description")

        assert response.data.id == "prj-123"
        assert response.data.attributes["name"] == "test-project"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/organizations/test-org/projects" in call_args[1]["url"]
        assert call_args[1]["json"]["data"]["attributes"]["name"] == "test-project"

    @pytest.mark.asyncio
    async def test_update_project(self, config, mock_httpx_client):
        """Test project update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "prj-123",
                "type": "projects",
                "attributes": {"name": "updated-project"},
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.update_project("prj-123", name="updated-project")

        assert response.data.id == "prj-123"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "PATCH"
        assert "/projects/prj-123" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_list_projects(self, config, mock_httpx_client):
        """Test project listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "prj-123",
                    "type": "projects",
                    "attributes": {"name": "project-1"},
                },
                {
                    "id": "prj-456",
                    "type": "projects",
                    "attributes": {"name": "project-2"},
                },
            ]
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.list_projects()

        assert len(response.data) == 2
        assert response.data[0].id == "prj-123"
        assert response.data[1].id == "prj-456"

    @pytest.mark.asyncio
    async def test_get_project(self, config, mock_httpx_client):
        """Test getting a specific project."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "prj-123",
                "type": "projects",
                "attributes": {"name": "test-project"},
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.get_project("prj-123")

        assert response.data.id == "prj-123"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "/projects/prj-123" in call_args[1]["url"]


class TestWorkspaceMethods:
    """Test workspace management methods."""

    @pytest.mark.asyncio
    async def test_create_workspace(self, config, mock_httpx_client):
        """Test workspace creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace", "auto-apply": True},
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.create_workspace("test-workspace", auto_apply=True)

        assert response.data.id == "ws-123"
        assert response.data.attributes["name"] == "test-workspace"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/organizations/test-org/workspaces" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_lock_workspace(self, config, mock_httpx_client):
        """Test workspace locking."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": "lock-123", "type": "workspace-locks"}
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.lock_workspace("ws-123", "Maintenance")

        assert response.data.id == "lock-123"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/workspaces/ws-123/actions/lock" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_unlock_workspace(self, config, mock_httpx_client):
        """Test workspace unlocking."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"locked": False},
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.unlock_workspace("ws-123")

        assert response.data.id == "ws-123"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/workspaces/ws-123/actions/unlock" in call_args[1]["url"]


class TestRunMethods:
    """Test run management methods."""

    @pytest.mark.asyncio
    async def test_create_run(self, config, mock_httpx_client):
        """Test run creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {
                "id": "run-123",
                "type": "runs",
                "attributes": {"status": "planning", "message": "Test run"},
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.create_run("ws-123", "Test run")

        assert response.data.id == "run-123"
        assert response.data.attributes["status"] == "planning"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/runs" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_apply_run(self, config, mock_httpx_client):
        """Test run apply."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": "apply-123", "type": "applies"}
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.apply_run("run-123", "Apply comment")

        assert response.data.id == "apply-123"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/runs/run-123/actions/apply" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_cancel_run(self, config, mock_httpx_client):
        """Test run cancellation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "run-123",
                "type": "runs",
                "attributes": {"status": "canceled"},
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.cancel_run("run-123")

        assert response.data.id == "run-123"

        # Verify the request was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/runs/run-123/actions/cancel" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_list_runs(self, config, mock_httpx_client):
        """Test run listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "run-123", "type": "runs", "attributes": {"status": "applied"}},
                {"id": "run-456", "type": "runs", "attributes": {"status": "planning"}},
            ]
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.list_runs(workspace_id="ws-123")

        assert len(response.data) == 2
        assert response.data[0].id == "run-123"
        assert response.data[1].id == "run-456"
