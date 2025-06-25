"""Pydantic models for HCP Terraform API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class JsonApiLinks(BaseModel):
    """JSON API links object."""

    self: Optional[str] = Field(None, description="Link to the current resource.")
    first: Optional[str] = Field(
        None, description="Link to the first page of a collection."
    )
    prev: Optional[str] = Field(
        None, description="Link to the previous page of a collection."
    )
    next: Optional[str] = Field(
        None, description="Link to the next page of a collection."
    )
    last: Optional[str] = Field(
        None, description="Link to the last page of a collection."
    )


class JsonApiMeta(BaseModel):
    """JSON API meta object."""

    pagination: Optional[Dict[str, Any]] = Field(
        None, description="Pagination metadata."
    )


class JsonApiError(BaseModel):
    """JSON API error object."""

    id: Optional[str] = Field(
        None,
        description="A unique identifier for this particular occurrence of the problem.",
    )
    status: Optional[str] = Field(
        None, description="The HTTP status code applicable to this problem."
    )
    code: Optional[str] = Field(None, description="An application-specific error code.")
    title: Optional[str] = Field(
        None, description="A short, human-readable summary of the problem."
    )
    detail: Optional[str] = Field(
        None,
        description="A human-readable explanation specific to this occurrence of the problem.",
    )
    source: Optional[Dict[str, Any]] = Field(
        None, description="An object containing references to the source of the error."
    )


class JsonApiResource(BaseModel):
    """Base JSON API resource object."""

    id: str = Field(..., description="The resource's unique identifier.")
    type: str = Field(..., description="The resource's type.")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="The resource's attributes."
    )
    relationships: Optional[Dict[str, Any]] = Field(
        None, description="The resource's relationships to other resources."
    )
    links: Optional[JsonApiLinks] = Field(
        None, description="Links related to the resource."
    )


class JsonApiResponse(BaseModel):
    """JSON API response wrapper."""

    data: Optional[Union[JsonApiResource, List[JsonApiResource]]] = Field(
        None, description="The response's primary data."
    )
    included: Optional[List[JsonApiResource]] = Field(
        None,
        description="An array of resource objects that are related to the primary data.",
    )
    errors: Optional[List[JsonApiError]] = Field(
        None, description="An array of error objects."
    )
    links: Optional[JsonApiLinks] = Field(
        None, description="Links related to the primary data."
    )
    meta: Optional[JsonApiMeta] = Field(
        None, description="Non-standard meta-information about the response."
    )


# Terraform-specific models
class ProjectAttributes(BaseModel):
    """Project attributes."""

    name: str = Field(..., description="The name of the project.")
    description: Optional[str] = Field(
        None, description="The description of the project."
    )
    auto_destroy_activity_duration: Optional[str] = Field(
        None,
        description="The duration after which to automatically destroy ephemeral workspaces.",
    )
    created_at: Optional[datetime] = Field(
        None, description="The timestamp when the project was created."
    )
    updated_at: Optional[datetime] = Field(
        None, description="The timestamp when the project was last updated."
    )


class WorkspaceAttributes(BaseModel):
    """Workspace attributes."""

    name: str = Field(..., description="The name of the workspace.")
    description: Optional[str] = Field(
        None, description="The description of the workspace."
    )
    auto_apply: Optional[bool] = Field(
        None, description="Whether to automatically apply changes."
    )
    execution_mode: Optional[str] = Field(
        None,
        description="The execution mode of the workspace (e.g., 'remote', 'local', 'agent').",
    )
    terraform_version: Optional[str] = Field(
        None, description="The version of Terraform to use for this workspace."
    )
    working_directory: Optional[str] = Field(
        None, description="The working directory for this workspace."
    )
    trigger_prefixes: Optional[List[str]] = Field(
        None, description="A list of file paths that trigger a run."
    )
    locked: Optional[bool] = Field(None, description="Whether the workspace is locked.")
    created_at: Optional[datetime] = Field(
        None, description="The timestamp when the workspace was created."
    )
    updated_at: Optional[datetime] = Field(
        None, description="The timestamp when the workspace was last updated."
    )


class RunAttributes(BaseModel):
    """Run attributes."""

    status: Optional[str] = Field(None, description="The status of the run.")
    status_timestamps: Optional[Dict[str, datetime]] = Field(
        None, description="Timestamps for various run statuses."
    )
    message: Optional[str] = Field(
        None, description="The message associated with the run."
    )
    terraform_version: Optional[str] = Field(
        None, description="The version of Terraform used for this run."
    )
    auto_apply: Optional[bool] = Field(
        None, description="Whether the run will auto-apply."
    )
    is_destroy: Optional[bool] = Field(
        None, description="Whether this is a destroy run."
    )
    refresh: Optional[bool] = Field(
        None, description="Whether to refresh the state before planning."
    )
    refresh_only: Optional[bool] = Field(
        None, description="Whether this is a refresh-only run."
    )
    replace_addrs: Optional[List[str]] = Field(
        None, description="A list of resource addresses to replace."
    )
    target_addrs: Optional[List[str]] = Field(
        None, description="A list of resource addresses to target."
    )
    created_at: Optional[datetime] = Field(
        None, description="The timestamp when the run was created."
    )
    plan_only: Optional[bool] = Field(
        None, description="Whether this is a plan-only run."
    )


# Request models for creating resources
class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""

    name: str = Field(..., description="The name of the project to create.")
    description: Optional[str] = Field(
        None, description="The description of the project."
    )


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""

    name: Optional[str] = Field(None, description="The new name of the project.")
    description: Optional[str] = Field(
        None, description="The new description of the project."
    )


class CreateWorkspaceRequest(BaseModel):
    """Request model for creating a workspace."""

    name: str = Field(..., description="The name of the workspace to create.")
    project_id: Optional[str] = Field(
        None, description="The ID of the project to associate the workspace with."
    )
    description: Optional[str] = Field(
        None, description="The description of the workspace."
    )
    auto_apply: Optional[bool] = Field(
        None, description="Whether to enable auto-apply."
    )
    execution_mode: Optional[str] = Field(
        None, description="The execution mode (e.g., 'remote', 'local', 'agent')."
    )
    terraform_version: Optional[str] = Field(
        None, description="The Terraform version to use."
    )
    working_directory: Optional[str] = Field(None, description="The working directory.")
    trigger_prefixes: Optional[List[str]] = Field(
        None, description="A list of file paths that trigger a run."
    )


class UpdateWorkspaceRequest(BaseModel):
    """Request model for updating a workspace."""

    name: Optional[str] = Field(None, description="The new name of the workspace.")
    description: Optional[str] = Field(
        None, description="The new description of the workspace."
    )
    auto_apply: Optional[bool] = Field(
        None, description="Whether to enable auto-apply."
    )
    execution_mode: Optional[str] = Field(None, description="The execution mode.")
    terraform_version: Optional[str] = Field(
        None, description="The Terraform version to use."
    )
    working_directory: Optional[str] = Field(None, description="The working directory.")
    trigger_prefixes: Optional[List[str]] = Field(
        None, description="A list of file paths that trigger a run."
    )


class CreateRunRequest(BaseModel):
    """Request model for creating a run."""

    workspace_id: str = Field(
        ..., description="The ID of the workspace to create the run in."
    )
    message: Optional[str] = Field(None, description="The message for the run.")
    is_destroy: Optional[bool] = Field(
        None, description="Whether this is a destroy run."
    )
    refresh: Optional[bool] = Field(
        None, description="Whether to refresh the state before planning."
    )
    refresh_only: Optional[bool] = Field(
        None, description="Whether this is a refresh-only run."
    )
    replace_addrs: Optional[List[str]] = Field(
        None, description="A list of resource addresses to replace."
    )
    target_addrs: Optional[List[str]] = Field(
        None, description="A list of resource addresses to target."
    )
    plan_only: Optional[bool] = Field(
        None, description="Whether this is a plan-only run."
    )


class LockWorkspaceRequest(BaseModel):
    """Request model for locking a workspace."""

    reason: Optional[str] = Field(
        None, description="The reason for locking the workspace."
    )


class RunActionRequest(BaseModel):
    """Request model for run actions (apply, cancel, discard)."""

    comment: Optional[str] = Field(None, description="A comment for the action.")
