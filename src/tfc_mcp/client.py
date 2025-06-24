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
            now = asyncio.get_event_loop().time()
            # Remove old requests outside the window
            self.requests = [req_time for req_time in self.requests if now - req_time < self.window_seconds]
            
            if len(self.requests) >= self.max_requests:
                # Calculate sleep time
                sleep_time = self.window_seconds - (now - self.requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    return await self.acquire()
            
            self.requests.append(now)


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