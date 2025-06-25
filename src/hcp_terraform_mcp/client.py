"""HCP Terraform API client."""

import asyncio
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, ValidationError

from .config import TerraformConfig
from .models import (
    CreateProjectRequest,
    CreateRunRequest,
    CreateWorkspaceRequest,
    JsonApiError,
    JsonApiResponse,
    RunActionRequest,
    UpdateProjectRequest,
    UpdateWorkspaceRequest,
)


class TerraformApiError(Exception):
    """Exception raised for Terraform API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        errors: Optional[List[JsonApiError]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire rate limit token."""
        async with self._lock:
            while True:
                now = asyncio.get_event_loop().time()
                self.requests = [
                    req_time
                    for req_time in self.requests
                    if now - req_time < self.window_seconds
                ]

                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    break

                sleep_time = self.window_seconds - (now - self.requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)


class Endpoints:
    """Manages API endpoint URLs."""

    def __init__(self, organization: str):
        self.organization = organization

    def organization_details(self) -> str:
        """Endpoint for organization details."""
        return f"/organizations/{self.organization}"

    def projects(self) -> str:
        """Endpoint for listing or creating projects."""
        return f"/organizations/{self.organization}/projects"

    def project(self, project_id: str) -> str:
        """Endpoint for a specific project."""
        return f"/projects/{project_id}"

    def workspaces(self) -> str:
        """Endpoint for listing or creating workspaces."""
        return f"/organizations/{self.organization}/workspaces"

    def workspace(self, workspace_id: str) -> str:
        """Endpoint for a specific workspace."""
        return f"/workspaces/{workspace_id}"

    def lock_workspace(self, workspace_id: str) -> str:
        """Endpoint for locking a workspace."""
        return f"/workspaces/{workspace_id}/actions/lock"

    def unlock_workspace(self, workspace_id: str) -> str:
        """Endpoint for unlocking a workspace."""
        return f"/workspaces/{workspace_id}/actions/unlock"

    def runs(self) -> str:
        """Endpoint for creating a run."""
        return "/runs"

    def organization_runs(self) -> str:
        """Endpoint for listing organization-level runs."""
        return f"/organizations/{self.organization}/runs"

    def workspace_runs(self, workspace_id: str) -> str:
        """Endpoint for listing workspace-level runs."""
        return f"/workspaces/{workspace_id}/runs"

    def run(self, run_id: str) -> str:
        """Endpoint for a specific run."""
        return f"/runs/{run_id}"

    def apply_run(self, run_id: str) -> str:
        """Endpoint for applying a run."""
        return f"/runs/{run_id}/actions/apply"

    def cancel_run(self, run_id: str) -> str:
        """Endpoint for canceling a run."""
        return f"/runs/{run_id}/actions/cancel"

    def discard_run(self, run_id: str) -> str:
        """Endpoint for discarding a run."""
        return f"/runs/{run_id}/actions/discard"


class TerraformClient:
    """HCP Terraform API client."""

    def __init__(self, config: TerraformConfig):
        self.config = config
        self.rate_limiter = RateLimiter()
        self.endpoints = Endpoints(config.organization)
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_token}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            },
            timeout=30.0,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _handle_api_error(
        self, response: httpx.Response, api_response: JsonApiResponse
    ):
        """Construct and raise a TerraformApiError."""
        error_message = f"API request failed with status {response.status_code}"
        if api_response.errors:
            error_details = "; ".join(
                [
                    f"{err.title}: {err.detail}"
                    for err in api_response.errors
                    if err.title and err.detail
                ]
            )
            if error_details:
                error_message += f": {error_details}"
        raise TerraformApiError(
            error_message, response.status_code, api_response.errors
        )

    def _handle_api_error(
        self, response: httpx.Response, api_response: JsonApiResponse
    ):
        """Construct and raise a TerraformApiError."""
        error_message = f"API request failed with status {response.status_code}"
        if api_response.errors:
            error_details = "; ".join(
                [
                    f"{err.title}: {err.detail}"
                    for err in api_response.errors
                    if err.title and err.detail
                ]
            )
            if error_details:
                error_message += f": {error_details}"
        raise TerraformApiError(
            error_message, response.status_code, api_response.errors
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> JsonApiResponse:
        """Make an authenticated request to the Terraform API."""
        await self.rate_limiter.acquire()
        try:
            response = await self._client.request(
                method=method, url=endpoint, json=data, params=params
            )
            try:
                api_response = JsonApiResponse(**response.json())
            except (ValueError, ValidationError) as e:
                raise TerraformApiError(
                    f"Invalid JSON response: {e}", response.status_code
                )

            if response.status_code >= 400:
                self._handle_api_error(response, api_response)

            return api_response
        except httpx.RequestError as e:
            raise TerraformApiError(f"Request failed: {e}")

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> JsonApiResponse:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> JsonApiResponse:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, data=data)

    async def patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> JsonApiResponse:
        """Make a PATCH request."""
        return await self._make_request("PATCH", endpoint, data=data)

    async def delete(self, endpoint: str) -> JsonApiResponse:
        """Make a DELETE request."""
        return await self._make_request("DELETE", endpoint)

    async def health_check(self) -> bool:
        """Check if the API is accessible."""
        try:
            await self.get(self.endpoints.organization_details())
            return True
        except TerraformApiError:
            return False

    def _build_payload(self, type_name: str, model: BaseModel) -> Dict[str, Any]:
        """Build a JSON:API compliant payload from a Pydantic model."""
        return {
            "data": {
                "type": type_name,
                "attributes": model.model_dump(exclude_unset=True),
            }
        }

    # Project management methods
    async def create_project(
        self, project_data: CreateProjectRequest
    ) -> JsonApiResponse:
        """Create a new project in the organization."""
        payload = self._build_payload("projects", project_data)
        return await self.post(self.endpoints.projects(), payload)

    async def update_project(
        self, project_id: str, project_data: UpdateProjectRequest
    ) -> JsonApiResponse:
        """Update an existing project."""
        if not project_data.model_dump(exclude_unset=True):
            raise ValueError("At least one attribute to update must be provided.")
        payload = self._build_payload("projects", project_data)
        return await self.patch(self.endpoints.project(project_id), payload)

    async def list_projects(
        self, include: Optional[str] = None, search: Optional[str] = None
    ) -> JsonApiResponse:
        """List projects in the organization."""
        params = {}
        if include:
            params["include"] = include
        if search:
            params["search[names]"] = search
        return await self.get(self.endpoints.projects(), params)

    async def get_project(self, project_id: str) -> JsonApiResponse:
        """Get a specific project by ID."""
        return await self.get(self.endpoints.project(project_id))

    # Workspace management methods
    async def create_workspace(
        self, workspace_data: CreateWorkspaceRequest
    ) -> JsonApiResponse:
        """Create a new workspace in the organization."""
        attributes = workspace_data.model_dump(exclude_unset=True, by_alias=True)
        payload = {"data": {"type": "workspaces", "attributes": attributes}}
        if workspace_data.project_id:
            payload["data"]["relationships"] = {
                "project": {
                    "data": {"type": "projects", "id": workspace_data.project_id}
                }
            }
        return await self.post(self.endpoints.workspaces(), payload)

    async def update_workspace(
        self, workspace_id: str, workspace_data: UpdateWorkspaceRequest
    ) -> JsonApiResponse:
        """Update an existing workspace."""
        if not workspace_data.model_dump(exclude_unset=True):
            raise ValueError("At least one attribute to update must be provided.")
        payload = self._build_payload("workspaces", workspace_data)
        return await self.patch(self.endpoints.workspace(workspace_id), payload)

    async def list_workspaces(
        self, include: Optional[str] = None, search: Optional[str] = None
    ) -> JsonApiResponse:
        """List workspaces in the organization."""
        params = {}
        if include:
            params["include"] = include
        if search:
            params["search[name]"] = search
        return await self.get(self.endpoints.workspaces(), params)

    async def get_workspace(self, workspace_id: str) -> JsonApiResponse:
        """Get a specific workspace by ID."""
        return await self.get(self.endpoints.workspace(workspace_id))

    async def lock_workspace(
        self, workspace_id: str, reason: Optional[str] = None
    ) -> JsonApiResponse:
        """Lock a workspace."""
        data = {"reason": reason} if reason else {}
        return await self.post(self.endpoints.lock_workspace(workspace_id), data)

    async def unlock_workspace(self, workspace_id: str) -> JsonApiResponse:
        """Unlock a workspace."""
        return await self.post(self.endpoints.unlock_workspace(workspace_id), {})

    # Run management methods
    async def create_run(self, run_data: CreateRunRequest) -> JsonApiResponse:
        """Create a new run for a workspace."""
        attributes = run_data.model_dump(exclude_unset=True, by_alias=True)
        workspace_id = attributes.pop("workspace_id")
        payload = {
            "data": {
                "type": "runs",
                "attributes": attributes,
                "relationships": {
                    "workspace": {"data": {"type": "workspaces", "id": workspace_id}}
                },
            }
        }
        return await self.post(self.endpoints.runs(), payload)

    async def apply_run(
        self, run_id: str, action_data: RunActionRequest
    ) -> JsonApiResponse:
        """Apply a run."""
        payload = {"comment": action_data.comment} if action_data.comment else {}
        return await self.post(self.endpoints.apply_run(run_id), payload)

    async def cancel_run(
        self, run_id: str, action_data: RunActionRequest
    ) -> JsonApiResponse:
        """Cancel a run."""
        payload = {"comment": action_data.comment} if action_data.comment else {}
        return await self.post(self.endpoints.cancel_run(run_id), payload)

    async def discard_run(
        self, run_id: str, action_data: RunActionRequest
    ) -> JsonApiResponse:
        """Discard a run."""
        payload = {"comment": action_data.comment} if action_data.comment else {}
        return await self.post(self.endpoints.discard_run(run_id), payload)

    async def list_runs(
        self,
        workspace_id: Optional[str] = None,
        organization_runs: bool = False,
        include: Optional[str] = None,
        search: Optional[str] = None,
    ) -> JsonApiResponse:
        """List runs for a workspace or organization."""
        params = {}
        if include:
            params["include"] = include
        if search:
            params["search"] = search

        if organization_runs:
            endpoint = self.endpoints.organization_runs()
        elif workspace_id:
            endpoint = self.endpoints.workspace_runs(workspace_id)
        else:
            raise ValueError(
                "Either workspace_id must be provided or organization_runs must be True"
            )
        return await self.get(endpoint, params)

    async def get_run(self, run_id: str) -> JsonApiResponse:
        """Get a specific run by ID."""
        return await self.get(self.endpoints.run(run_id))
