"""Tests for the Terraform API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.hcp_terraform_mcp.client import RateLimiter, TerraformApiError, TerraformClient
from src.hcp_terraform_mcp.config import TerraformConfig
from src.hcp_terraform_mcp.models import (
    CreateProjectRequest,
    CreateRunRequest,
    CreateWorkspaceRequest,
    JsonApiResponse,
    RunActionRequest,
    UpdateProjectRequest,
)


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
    with patch("src.hcp_terraform_mcp.client.httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


class TestRateLimiter:
    """Test rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        await limiter.acquire()
        await limiter.acquire()

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excess_requests(self):
        """Test that rate limiter blocks requests exceeding limit."""
        limiter = RateLimiter(max_requests=1, window_seconds=0.05)
        await limiter.acquire()
        import time

        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time
        assert 0.03 < elapsed < 0.2


class TestTerraformClient:
    """Test Terraform API client."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, config):
        """Test client initialization."""
        client = TerraformClient(config)
        assert client.config == config
        assert client.rate_limiter is not None
        assert client.endpoints.organization == "test-org"

    @pytest.mark.asyncio
    async def test_successful_get_request(self, config, mock_httpx_client):
        """Test successful GET request."""
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

        assert isinstance(response, JsonApiResponse)
        assert response.data.id == "test-id"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, config, mock_httpx_client):
        """Test API error handling."""
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
        assert await client.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, config, mock_httpx_client):
        """Test failed health check."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"errors": [{"title": "Unauthorized"}]}
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        assert await client.health_check() is False


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
                "attributes": {"name": "test-project"},
            }
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        project_data = CreateProjectRequest(name="test-project")
        response = await client.create_project(project_data)

        assert response.data.id == "prj-123"
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "POST"
        assert call_args.kwargs["url"] == "/organizations/test-org/projects"
        assert call_args.kwargs["json"]["data"]["attributes"]["name"] == "test-project"

    @pytest.mark.asyncio
    async def test_update_project(self, config, mock_httpx_client):
        """Test project update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": "prj-123", "type": "projects"}
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        project_data = UpdateProjectRequest(name="updated-project")
        await client.update_project("prj-123", project_data)

        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "PATCH"
        assert call_args.kwargs["url"] == "/projects/prj-123"

    @pytest.mark.asyncio
    async def test_list_projects(self, config, mock_httpx_client):
        """Test project listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "prj-1", "type": "projects"},
                {"id": "prj-2", "type": "projects"},
            ]
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        response = await client.list_projects()

        assert len(response.data) == 2


class TestWorkspaceMethods:
    """Test workspace management methods."""

    @pytest.mark.asyncio
    async def test_create_workspace(self, config, mock_httpx_client):
        """Test workspace creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {"id": "ws-123", "type": "workspaces"}
        }
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        workspace_data = CreateWorkspaceRequest(name="test-workspace", auto_apply=True)
        response = await client.create_workspace(workspace_data)

        assert response.data.id == "ws-123"
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "POST"
        assert call_args.kwargs["url"] == "/organizations/test-org/workspaces"

    @pytest.mark.asyncio
    async def test_lock_unlock_workspace(self, config, mock_httpx_client):
        """Test workspace locking and unlocking."""
        mock_httpx_client.request.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": {"id": "lock-123", "type": "workspace-locks"}},
        )
        client = TerraformClient(config)

        await client.lock_workspace("ws-123", "Maintenance")
        mock_httpx_client.request.assert_called_with(
            method="POST",
            url="/workspaces/ws-123/actions/lock",
            json={"reason": "Maintenance"},
            params=None,
        )

        mock_httpx_client.request.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": {"id": "ws-123", "type": "workspaces"}},
        )
        await client.unlock_workspace("ws-123")
        mock_httpx_client.request.assert_called_with(
            method="POST", url="/workspaces/ws-123/actions/unlock", json={}, params=None
        )


class TestRunMethods:
    """Test run management methods."""

    @pytest.mark.asyncio
    async def test_create_run(self, config, mock_httpx_client):
        """Test run creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "run-123", "type": "runs"}}
        mock_httpx_client.request.return_value = mock_response

        client = TerraformClient(config)
        run_data = CreateRunRequest(workspace_id="ws-123", message="Test run")
        response = await client.create_run(run_data)

        assert response.data.id == "run-123"
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "POST"
        assert call_args.kwargs["url"] == "/runs"

    @pytest.mark.asyncio
    async def test_run_actions(self, config, mock_httpx_client):
        """Test run actions like apply, cancel, discard."""
        mock_httpx_client.request.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": {"id": "apply-123", "type": "applies"}},
        )
        client = TerraformClient(config)
        action_data = RunActionRequest(comment="Test comment")

        await client.apply_run("run-123", action_data)
        mock_httpx_client.request.assert_called_with(
            method="POST",
            url="/runs/run-123/actions/apply",
            json={"comment": "Test comment"},
            params=None,
        )

        mock_httpx_client.request.return_value = MagicMock(
            status_code=200, json=lambda: {"data": {"id": "run-123", "type": "runs"}}
        )
        await client.cancel_run("run-123", action_data)
        mock_httpx_client.request.assert_called_with(
            method="POST",
            url="/runs/run-123/actions/cancel",
            json={"comment": "Test comment"},
            params=None,
        )

        await client.discard_run("run-123", action_data)
        mock_httpx_client.request.assert_called_with(
            method="POST",
            url="/runs/run-123/actions/discard",
            json={"comment": "Test comment"},
            params=None,
        )
