"""Pydantic models for HCP Terraform API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class JsonApiLinks(BaseModel):
    """JSON API links object."""

    self: Optional[str] = None
    first: Optional[str] = None
    prev: Optional[str] = None
    next: Optional[str] = None
    last: Optional[str] = None


class JsonApiMeta(BaseModel):
    """JSON API meta object."""

    pagination: Optional[Dict[str, Any]] = None


class JsonApiError(BaseModel):
    """JSON API error object."""

    id: Optional[str] = None
    status: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    source: Optional[Dict[str, Any]] = None


class JsonApiResource(BaseModel):
    """Base JSON API resource object."""

    id: str
    type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: Optional[Dict[str, Any]] = None
    links: Optional[JsonApiLinks] = None


class JsonApiResponse(BaseModel):
    """JSON API response wrapper."""

    data: Optional[Union[JsonApiResource, List[JsonApiResource]]] = None
    included: Optional[List[JsonApiResource]] = None
    errors: Optional[List[JsonApiError]] = None
    links: Optional[JsonApiLinks] = None
    meta: Optional[JsonApiMeta] = None


# Terraform-specific models
class ProjectAttributes(BaseModel):
    """Project attributes."""

    name: str
    description: Optional[str] = None
    auto_destroy_activity_duration: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkspaceAttributes(BaseModel):
    """Workspace attributes."""

    name: str
    description: Optional[str] = None
    auto_apply: Optional[bool] = None
    execution_mode: Optional[str] = None
    terraform_version: Optional[str] = None
    working_directory: Optional[str] = None
    trigger_prefixes: Optional[List[str]] = None
    locked: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RunAttributes(BaseModel):
    """Run attributes."""

    status: Optional[str] = None
    status_timestamps: Optional[Dict[str, datetime]] = None
    message: Optional[str] = None
    terraform_version: Optional[str] = None
    auto_apply: Optional[bool] = None
    is_destroy: Optional[bool] = None
    refresh: Optional[bool] = None
    refresh_only: Optional[bool] = None
    replace_addrs: Optional[List[str]] = None
    target_addrs: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    plan_only: Optional[bool] = None


# Request models for creating resources
class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""

    name: str
    description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""

    name: Optional[str] = None
    description: Optional[str] = None


class CreateWorkspaceRequest(BaseModel):
    """Request model for creating a workspace."""

    name: str
    project_id: Optional[str] = None
    description: Optional[str] = None
    auto_apply: Optional[bool] = None
    execution_mode: Optional[str] = None
    terraform_version: Optional[str] = None
    working_directory: Optional[str] = None
    trigger_prefixes: Optional[List[str]] = None


class UpdateWorkspaceRequest(BaseModel):
    """Request model for updating a workspace."""

    name: Optional[str] = None
    description: Optional[str] = None
    auto_apply: Optional[bool] = None
    execution_mode: Optional[str] = None
    terraform_version: Optional[str] = None
    working_directory: Optional[str] = None
    trigger_prefixes: Optional[List[str]] = None


class CreateRunRequest(BaseModel):
    """Request model for creating a run."""

    workspace_id: str
    message: Optional[str] = None
    is_destroy: Optional[bool] = None
    refresh: Optional[bool] = None
    refresh_only: Optional[bool] = None
    replace_addrs: Optional[List[str]] = None
    target_addrs: Optional[List[str]] = None
    plan_only: Optional[bool] = None


class LockWorkspaceRequest(BaseModel):
    """Request model for locking a workspace."""

    reason: Optional[str] = None


class RunActionRequest(BaseModel):
    """Request model for run actions (apply, cancel, discard)."""

    comment: Optional[str] = None
