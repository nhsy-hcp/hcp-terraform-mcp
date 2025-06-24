"""HCP Terraform API client."""

import asyncio
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from .config import TerraformConfig
from .models import JsonApiResponse, JsonApiError


class TerraformApiError(Exception):
    """Exception raised for Terraform API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, errors: Optional[List[JsonApiError]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit token."""
        async with self._lock:
            while True:
                now = asyncio.get_event_loop().time()
                # Remove old requests outside the window
                self.requests = [req_time for req_time in self.requests if now - req_time < self.window_seconds]
                
                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    break
                
                # Calculate sleep time
                sleep_time = self.window_seconds - (now - self.requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)


class TerraformClient:
    """HCP Terraform API client."""
    
    def __init__(self, config: TerraformConfig):
        self.config = config
        self.rate_limiter = RateLimiter()
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
                method=method,
                url=endpoint,
                json=data,
                params=params,
            )
            
            # Parse response
            try:
                response_data = response.json()
                api_response = JsonApiResponse(**response_data)
            except (ValueError, ValidationError) as e:
                raise TerraformApiError(f"Invalid JSON response: {e}", response.status_code)
            
            # Check for API errors
            if response.status_code >= 400:
                error_message = f"API request failed with status {response.status_code}"
                if api_response.errors:
                    error_details = "; ".join([
                        f"{err.title}: {err.detail}" for err in api_response.errors
                        if err.title and err.detail
                    ])
                    if error_details:
                        error_message += f": {error_details}"
                
                raise TerraformApiError(error_message, response.status_code, api_response.errors)
            
            return api_response
            
        except httpx.RequestError as e:
            raise TerraformApiError(f"Request failed: {e}")
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> JsonApiResponse:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> JsonApiResponse:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, data=data)
    
    async def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> JsonApiResponse:
        """Make a PATCH request."""
        return await self._make_request("PATCH", endpoint, data=data)
    
    async def delete(self, endpoint: str) -> JsonApiResponse:
        """Make a DELETE request."""
        return await self._make_request("DELETE", endpoint)
    
    # Organization endpoints
    def get_organization_endpoint(self, path: str = "") -> str:
        """Get organization-scoped endpoint."""
        base = f"/organizations/{self.config.organization}"
        return f"{base}/{path}".rstrip("/")
    
    # Health check
    async def health_check(self) -> bool:
        """Check if the API is accessible."""
        try:
            await self.get(self.get_organization_endpoint())
            return True
        except TerraformApiError:
            return False
    
    # Project management methods
    async def create_project(self, name: str, description: Optional[str] = None) -> JsonApiResponse:
        """Create a new project in the organization."""
        data = {
            "data": {
                "type": "projects",
                "attributes": {
                    "name": name
                }
            }
        }
        
        if description:
            data["data"]["attributes"]["description"] = description
        
        endpoint = self.get_organization_endpoint("projects")
        return await self.post(endpoint, data)
    
    async def update_project(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> JsonApiResponse:
        """Update an existing project."""
        attributes = {}
        if name:
            attributes["name"] = name
        if description:
            attributes["description"] = description
        
        if not attributes:
            raise ValueError("At least one attribute (name or description) must be provided")
        
        data = {
            "data": {
                "type": "projects",
                "attributes": attributes
            }
        }
        
        endpoint = f"/projects/{project_id}"
        return await self.patch(endpoint, data)
    
    async def list_projects(self, include: Optional[str] = None, search: Optional[str] = None) -> JsonApiResponse:
        """List projects in the organization."""
        params = {}
        if include:
            params["include"] = include
        if search:
            params["search"] = search
        
        endpoint = self.get_organization_endpoint("projects")
        return await self.get(endpoint, params)
    
    async def get_project(self, project_id: str) -> JsonApiResponse:
        """Get a specific project by ID."""
        endpoint = f"/projects/{project_id}"
        return await self.get(endpoint)
    
    # Workspace management methods
    async def create_workspace(
        self, 
        name: str, 
        project_id: Optional[str] = None,
        description: Optional[str] = None,
        auto_apply: Optional[bool] = None,
        execution_mode: Optional[str] = None,
        terraform_version: Optional[str] = None,
        working_directory: Optional[str] = None,
        **kwargs
    ) -> JsonApiResponse:
        """Create a new workspace in the organization."""
        attributes = {"name": name}
        
        if description:
            attributes["description"] = description
        if auto_apply is not None:
            attributes["auto-apply"] = auto_apply
        if execution_mode:
            attributes["execution-mode"] = execution_mode
        if terraform_version:
            attributes["terraform-version"] = terraform_version
        if working_directory:
            attributes["working-directory"] = working_directory
        
        # Add any additional attributes from kwargs
        for key, value in kwargs.items():
            if value is not None:
                attributes[key.replace("_", "-")] = value
        
        data = {
            "data": {
                "type": "workspaces",
                "attributes": attributes
            }
        }
        
        # Add project relationship if specified
        if project_id:
            data["data"]["relationships"] = {
                "project": {
                    "data": {
                        "type": "projects",
                        "id": project_id
                    }
                }
            }
        
        endpoint = self.get_organization_endpoint("workspaces")
        return await self.post(endpoint, data)
    
    async def update_workspace(self, workspace_id: str, **kwargs) -> JsonApiResponse:
        """Update an existing workspace."""
        attributes = {}
        
        # Convert snake_case to kebab-case for API
        for key, value in kwargs.items():
            if value is not None:
                attributes[key.replace("_", "-")] = value
        
        if not attributes:
            raise ValueError("At least one attribute must be provided")
        
        data = {
            "data": {
                "type": "workspaces",
                "attributes": attributes
            }
        }
        
        endpoint = f"/workspaces/{workspace_id}"
        return await self.patch(endpoint, data)
    
    async def list_workspaces(self, include: Optional[str] = None, search: Optional[str] = None) -> JsonApiResponse:
        """List workspaces in the organization."""
        params = {}
        if include:
            params["include"] = include
        if search:
            params["search"] = search
        
        endpoint = self.get_organization_endpoint("workspaces")
        return await self.get(endpoint, params)
    
    async def get_workspace(self, workspace_id: str) -> JsonApiResponse:
        """Get a specific workspace by ID."""
        endpoint = f"/workspaces/{workspace_id}"
        return await self.get(endpoint)
    
    async def lock_workspace(self, workspace_id: str, reason: Optional[str] = None) -> JsonApiResponse:
        """Lock a workspace."""
        data = {
            "data": {
                "type": "workspace-locks",
                "attributes": {}
            }
        }
        
        if reason:
            data["data"]["attributes"]["reason"] = reason
        
        endpoint = f"/workspaces/{workspace_id}/actions/lock"
        return await self.post(endpoint, data)
    
    async def unlock_workspace(self, workspace_id: str) -> JsonApiResponse:
        """Unlock a workspace."""
        endpoint = f"/workspaces/{workspace_id}/actions/unlock"
        return await self.post(endpoint, {})
    
    # Run management methods
    async def create_run(
        self,
        workspace_id: str,
        message: Optional[str] = None,
        is_destroy: Optional[bool] = None,
        refresh: Optional[bool] = None,
        refresh_only: Optional[bool] = None,
        replace_addrs: Optional[List[str]] = None,
        target_addrs: Optional[List[str]] = None,
        plan_only: Optional[bool] = None,
        **kwargs
    ) -> JsonApiResponse:
        """Create a new run for a workspace."""
        attributes = {}
        
        if message:
            attributes["message"] = message
        if is_destroy is not None:
            attributes["is-destroy"] = is_destroy
        if refresh is not None:
            attributes["refresh"] = refresh
        if refresh_only is not None:
            attributes["refresh-only"] = refresh_only
        if replace_addrs:
            attributes["replace-addrs"] = replace_addrs
        if target_addrs:
            attributes["target-addrs"] = target_addrs
        if plan_only is not None:
            attributes["plan-only"] = plan_only
        
        # Add any additional attributes from kwargs
        for key, value in kwargs.items():
            if value is not None:
                attributes[key.replace("_", "-")] = value
        
        data = {
            "data": {
                "type": "runs",
                "attributes": attributes,
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workspace_id
                        }
                    }
                }
            }
        }
        
        endpoint = "/runs"
        return await self.post(endpoint, data)
    
    async def apply_run(self, run_id: str, comment: Optional[str] = None) -> JsonApiResponse:
        """Apply a run."""
        data = {
            "data": {
                "type": "applies",
                "attributes": {}
            }
        }
        
        if comment:
            data["data"]["attributes"]["comment"] = comment
        
        endpoint = f"/runs/{run_id}/actions/apply"
        return await self.post(endpoint, data)
    
    async def cancel_run(self, run_id: str, comment: Optional[str] = None) -> JsonApiResponse:
        """Cancel a run."""
        data = {
            "data": {
                "type": "runs",
                "attributes": {}
            }
        }
        
        if comment:
            data["data"]["attributes"]["comment"] = comment
        
        endpoint = f"/runs/{run_id}/actions/cancel"
        return await self.post(endpoint, data)
    
    async def discard_run(self, run_id: str, comment: Optional[str] = None) -> JsonApiResponse:
        """Discard a run."""
        data = {
            "data": {
                "type": "runs",
                "attributes": {}
            }
        }
        
        if comment:
            data["data"]["attributes"]["comment"] = comment
        
        endpoint = f"/runs/{run_id}/actions/discard"
        return await self.post(endpoint, data)
    
    async def list_runs(
        self, 
        workspace_id: Optional[str] = None, 
        organization_runs: bool = False,
        include: Optional[str] = None,
        search: Optional[str] = None
    ) -> JsonApiResponse:
        """List runs for a workspace or organization."""
        params = {}
        if include:
            params["include"] = include
        if search:
            params["search"] = search
        
        if organization_runs:
            endpoint = self.get_organization_endpoint("runs")
        elif workspace_id:
            endpoint = f"/workspaces/{workspace_id}/runs"
        else:
            raise ValueError("Either workspace_id must be provided or organization_runs must be True")
        
        return await self.get(endpoint, params)
    
    async def get_run(self, run_id: str) -> JsonApiResponse:
        """Get a specific run by ID."""
        endpoint = f"/runs/{run_id}"
        return await self.get(endpoint)