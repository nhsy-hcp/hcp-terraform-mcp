"""Resource handlers for the HCP Terraform MCP Server."""

import logging
from datetime import datetime
from typing import List

from mcp.types import AnyUrl, Resource, ReadResourceResult, TextResourceContents

from .client import TerraformClient, TerraformApiError
from .config import TerraformConfig
from .models import (
    OrganizationResourceData,
    ProjectResourceData,
    WorkspaceResourceData,
    RunResourceData,
    ResourceListData,
)

logger = logging.getLogger(__name__)


class ResourceHandler:
    """Handles listing and reading of MCP resources."""

    def __init__(self, client: TerraformClient, config: TerraformConfig):
        self.client = client
        self.config = config

    async def list_resources(self) -> List[Resource]:
        """List all available resources."""
        if self.config.debug_mode:
            logger.debug("Listing available resources")

        resources = [
            Resource(
                uri="terraform://organization/info",
                name="Organization Information",
                description="Basic information about the HCP Terraform organization",
                mimeType="application/json",
            ),
            # List-type resources
            Resource(
                uri="terraform://projects",
                name="Projects List",
                description="List of all projects in the organization",
                mimeType="application/json",
            ),
            Resource(
                uri="terraform://workspaces",
                name="Workspaces List",
                description="List of all workspaces in the organization",
                mimeType="application/json",
            ),
            Resource(
                uri="terraform://runs",
                name="Runs List",
                description="List of all runs in the organization",
                mimeType="application/json",
            ),
        ]

        try:
            # Add individual project resources
            projects_response = await self.client.list_projects()
            if projects_response.data:
                project_list = (
                    projects_response.data
                    if isinstance(projects_response.data, list)
                    else [projects_response.data]
                )
                for project in project_list:
                    resources.append(
                        Resource(
                            uri=f"terraform://project/{project.id}",
                            name=f"Project: {project.attributes.get('name', 'Unknown')}",
                            description=f"Details for project {project.id}",
                            mimeType="application/json",
                        )
                    )
        except TerraformApiError as e:
            logger.warning(f"Could not list project resources: {e}")

        try:
            # Add individual workspace resources
            workspaces_response = await self.client.list_workspaces()
            if workspaces_response.data:
                workspace_list = (
                    workspaces_response.data
                    if isinstance(workspaces_response.data, list)
                    else [workspaces_response.data]
                )
                for workspace in workspace_list:
                    resources.append(
                        Resource(
                            uri=f"terraform://workspace/{workspace.id}",
                            name=f"Workspace: {workspace.attributes.get('name', 'Unknown')}",
                            description=f"Details for workspace {workspace.id}",
                            mimeType="application/json",
                        )
                    )
        except TerraformApiError as e:
            logger.warning(f"Could not list workspace resources: {e}")

        try:
            # Add individual run resources (limit to recent runs to avoid too many resources)
            runs_response = await self.client.list_runs()
            if runs_response.data:
                run_list = (
                    runs_response.data
                    if isinstance(runs_response.data, list)
                    else [runs_response.data]
                )
                # Limit to first 50 runs to avoid overwhelming the resource list
                for run in run_list[:50]:
                    run_status = run.attributes.get("status", "unknown")
                    resources.append(
                        Resource(
                            uri=f"terraform://run/{run.id}",
                            name=f"Run: {run.id} ({run_status})",
                            description=f"Details for run {run.id} with status {run_status}",
                            mimeType="application/json",
                        )
                    )
        except TerraformApiError as e:
            logger.warning(f"Could not list run resources: {e}")

        return resources

    async def read_resource(self, uri: AnyUrl) -> ReadResourceResult:
        """Read a single resource by its URI."""
        uri_str = str(uri)
        if self.config.debug_mode:
            logger.debug(f"Reading resource: {uri_str}")

        try:
            current_time = datetime.now()

            # Organization information
            if uri_str == "terraform://organization/info":
                response = await self.client.get(
                    self.client.endpoints.organization_details()
                )
                if response.data:
                    org_data = OrganizationResourceData(
                        id=self.config.organization,
                        type="organization",
                        name=self.config.organization,
                        api_url=self.config.base_url,
                        status="connected",
                        retrieved_at=current_time,
                        attributes=response.data.attributes,
                    )
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=org_data.model_dump_json(indent=2),
                                mimeType="application/json",
                            )
                        ]
                    )

            # Individual project resource
            elif uri_str.startswith("terraform://project/"):
                project_id = uri_str.split("/")[-1]
                response = await self.client.get_project(project_id)
                if response.data:
                    # Try to get workspace count for this project
                    workspace_count = None
                    try:
                        workspaces = await self.client.list_workspaces()
                        if workspaces.data:
                            workspace_list = (
                                workspaces.data
                                if isinstance(workspaces.data, list)
                                else [workspaces.data]
                            )
                            workspace_count = sum(
                                1
                                for ws in workspace_list
                                if ws.relationships
                                and ws.relationships.get("project", {})
                                .get("data", {})
                                .get("id")
                                == project_id
                            )
                    except Exception:
                        pass  # Ignore errors getting workspace count

                    project_data = ProjectResourceData(
                        id=response.data.id,
                        type=response.data.type,
                        retrieved_at=current_time,
                        attributes=response.data.attributes,
                        relationships=response.data.relationships,
                        workspace_count=workspace_count,
                    )
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=project_data.model_dump_json(indent=2),
                                mimeType="application/json",
                            )
                        ]
                    )

            # Individual workspace resource
            elif uri_str.startswith("terraform://workspace/"):
                workspace_id = uri_str.split("/")[-1]
                response = await self.client.get_workspace(workspace_id)
                if response.data:
                    # Try to get latest run for this workspace
                    latest_run_id = None
                    try:
                        runs = await self.client.list_runs(workspace_id=workspace_id)
                        if runs.data:
                            run_list = (
                                runs.data
                                if isinstance(runs.data, list)
                                else [runs.data]
                            )
                            if run_list:
                                latest_run_id = run_list[0].id
                    except Exception:
                        pass  # Ignore errors getting latest run

                    workspace_data = WorkspaceResourceData(
                        id=response.data.id,
                        type=response.data.type,
                        retrieved_at=current_time,
                        attributes=response.data.attributes,
                        relationships=response.data.relationships,
                        latest_run_id=latest_run_id,
                    )
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=workspace_data.model_dump_json(indent=2),
                                mimeType="application/json",
                            )
                        ]
                    )

            # Individual run resource
            elif uri_str.startswith("terraform://run/"):
                run_id = uri_str.split("/")[-1]
                response = await self.client.get_run(run_id)
                if response.data:
                    # Try to get workspace name for this run
                    workspace_name = None
                    try:
                        if (
                            response.data.relationships
                            and response.data.relationships.get("workspace", {}).get(
                                "data"
                            )
                        ):
                            workspace_id = response.data.relationships["workspace"][
                                "data"
                            ]["id"]
                            workspace_response = await self.client.get_workspace(
                                workspace_id
                            )
                            if workspace_response.data:
                                workspace_name = workspace_response.data.attributes.get(
                                    "name"
                                )
                    except Exception:
                        pass  # Ignore errors getting workspace name

                    run_data = RunResourceData(
                        id=response.data.id,
                        type=response.data.type,
                        retrieved_at=current_time,
                        attributes=response.data.attributes,
                        relationships=response.data.relationships,
                        workspace_name=workspace_name,
                    )
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=run_data.model_dump_json(indent=2),
                                mimeType="application/json",
                            )
                        ]
                    )

            # Projects list
            elif uri_str == "terraform://projects":
                response = await self.client.list_projects()
                if response.data:
                    project_list = (
                        response.data
                        if isinstance(response.data, list)
                        else [response.data]
                    )
                    list_data = ResourceListData(
                        type="projects",
                        count=len(project_list),
                        retrieved_at=current_time,
                        resources=[proj.model_dump() for proj in project_list],
                        pagination=response.meta.pagination if response.meta else None,
                    )
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=list_data.model_dump_json(indent=2),
                                mimeType="application/json",
                            )
                        ]
                    )

            # Workspaces list
            elif uri_str == "terraform://workspaces":
                response = await self.client.list_workspaces()
                if response.data:
                    workspace_list = (
                        response.data
                        if isinstance(response.data, list)
                        else [response.data]
                    )
                    list_data = ResourceListData(
                        type="workspaces",
                        count=len(workspace_list),
                        retrieved_at=current_time,
                        resources=[ws.model_dump() for ws in workspace_list],
                        pagination=response.meta.pagination if response.meta else None,
                    )
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=list_data.model_dump_json(indent=2),
                                mimeType="application/json",
                            )
                        ]
                    )

            # Runs list
            elif uri_str == "terraform://runs":
                response = await self.client.list_runs()
                if response.data:
                    run_list = (
                        response.data
                        if isinstance(response.data, list)
                        else [response.data]
                    )
                    list_data = ResourceListData(
                        type="runs",
                        count=len(run_list),
                        retrieved_at=current_time,
                        resources=[run.model_dump() for run in run_list],
                        pagination=response.meta.pagination if response.meta else None,
                    )
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=list_data.model_dump_json(indent=2),
                                mimeType="application/json",
                            )
                        ]
                    )

            # Unknown resource
            return ReadResourceResult(
                contents=[
                    TextResourceContents(
                        uri=uri,
                        text=f"Unknown resource: {uri_str}",
                        mimeType="text/plain",
                    )
                ]
            )

        except TerraformApiError as e:
            logger.error(f"API Error reading resource {uri_str}: {e}")
            return ReadResourceResult(
                contents=[
                    TextResourceContents(
                        uri=uri, text=f"API Error: {e}", mimeType="text/plain"
                    )
                ]
            )
        except Exception as e:
            logger.exception(f"Unexpected error reading resource {uri_str}")
            return ReadResourceResult(
                contents=[
                    TextResourceContents(
                        uri=uri, text=f"Unexpected error: {e}", mimeType="text/plain"
                    )
                ]
            )
