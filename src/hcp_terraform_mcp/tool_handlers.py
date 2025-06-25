"""Tool handlers for the HCP Terraform MCP Server."""

from typing import Any, Dict, List

from .client import TerraformClient
from .models import (
    CreateProjectRequest,
    CreateRunRequest,
    CreateWorkspaceRequest,
    RunActionRequest,
    UpdateProjectRequest,
    UpdateWorkspaceRequest,
)
from mcp.types import TextContent


class ToolHandlers:
    """A dispatcher for tool calls."""

    def __init__(self, client: TerraformClient):
        self.client = client

    async def health_check(self, **kwargs: Any) -> List[TextContent]:
        """Check HCP Terraform API connectivity."""
        is_healthy = await self.client.health_check()
        status = "healthy" if is_healthy else "unhealthy"
        return [TextContent(type="text", text=f"HCP Terraform API is {status}")]

    async def create_project(self, **kwargs: Any) -> List[TextContent]:
        """Create a new HCP Terraform project."""
        request = CreateProjectRequest(**kwargs)
        response = await self.client.create_project(request)
        if response.data:
            return [
                TextContent(
                    type="text",
                    text=f"Successfully created project '{request.name}' with ID: {response.data.id}",
                )
            ]
        return [
            TextContent(type="text", text=f"Failed to create project '{request.name}'")
        ]

    async def update_project(self, **kwargs: Any) -> List[TextContent]:
        """Update an existing HCP Terraform project."""
        project_id = kwargs.pop("project_id")
        request = UpdateProjectRequest(**kwargs)
        response = await self.client.update_project(project_id, request)
        if response.data:
            return [
                TextContent(
                    type="text",
                    text=f"Successfully updated project {project_id}",
                )
            ]
        return [TextContent(type="text", text=f"Failed to update project {project_id}")]

    async def list_projects(self, **kwargs: Any) -> List[TextContent]:
        """List HCP Terraform projects in the organization."""
        response = await self.client.list_projects(**kwargs)
        if response.data:
            projects = (
                response.data if isinstance(response.data, list) else [response.data]
            )
            project_list = []
            for project in projects:
                project_info = (
                    f"- {project.attributes.get('name', 'Unknown')} (ID: {project.id})"
                )
                if project.attributes.get("description"):
                    project_info += f" - {project.attributes['description']}"
                project_list.append(project_info)
            projects_text = f"Found {len(projects)} project(s):\n" + "\n".join(
                project_list
            )
            return [TextContent(type="text", text=projects_text)]
        return [TextContent(type="text", text="No projects found")]

    async def create_workspace(self, **kwargs: Any) -> List[TextContent]:
        """Create a new HCP Terraform workspace."""
        request = CreateWorkspaceRequest(**kwargs)
        response = await self.client.create_workspace(request)
        if response.data:
            return [
                TextContent(
                    type="text",
                    text=f"Successfully created workspace '{request.name}' with ID: {response.data.id}",
                )
            ]
        return [
            TextContent(
                type="text", text=f"Failed to create workspace '{request.name}'"
            )
        ]

    async def update_workspace(self, **kwargs: Any) -> List[TextContent]:
        """Update an existing HCP Terraform workspace."""
        workspace_id = kwargs.pop("workspace_id")
        request = UpdateWorkspaceRequest(**kwargs)
        response = await self.client.update_workspace(workspace_id, request)
        if response.data:
            return [
                TextContent(
                    type="text",
                    text=f"Successfully updated workspace {workspace_id}",
                )
            ]
        return [
            TextContent(type="text", text=f"Failed to update workspace {workspace_id}")
        ]

    async def list_workspaces(self, **kwargs: Any) -> List[TextContent]:
        """List HCP Terraform workspaces in the organization."""
        response = await self.client.list_workspaces(**kwargs)
        if response.data:
            workspaces = (
                response.data if isinstance(response.data, list) else [response.data]
            )
            workspace_list = []
            for workspace in workspaces:
                workspace_info = f"- {workspace.attributes.get('name', 'Unknown')} (ID: {workspace.id})"
                if workspace.attributes.get("description"):
                    workspace_info += f" - {workspace.attributes['description']}"
                if workspace.attributes.get("locked"):
                    workspace_info += " [LOCKED]"
                workspace_list.append(workspace_info)
            workspaces_text = f"Found {len(workspaces)} workspace(s):\n" + "\n".join(
                workspace_list
            )
            return [TextContent(type="text", text=workspaces_text)]
        return [TextContent(type="text", text="No workspaces found")]

    async def lock_workspace(self, **kwargs: Any) -> List[TextContent]:
        """Lock an HCP Terraform workspace."""
        workspace_id = kwargs.get("workspace_id")
        reason = kwargs.get("reason")
        await self.client.lock_workspace(workspace_id, reason)
        return [
            TextContent(
                type="text", text=f"Successfully locked workspace {workspace_id}"
            )
        ]

    async def unlock_workspace(self, **kwargs: Any) -> List[TextContent]:
        """Unlock an HCP Terraform workspace."""
        workspace_id = kwargs.get("workspace_id")
        await self.client.unlock_workspace(workspace_id)
        return [
            TextContent(
                type="text", text=f"Successfully unlocked workspace {workspace_id}"
            )
        ]

    async def create_run(self, **kwargs: Any) -> List[TextContent]:
        """Create a new HCP Terraform run."""
        request = CreateRunRequest(**kwargs)
        response = await self.client.create_run(request)
        if response.data:
            return [
                TextContent(
                    type="text",
                    text=f"Successfully created run with ID: {response.data.id}",
                )
            ]
        return [TextContent(type="text", text="Failed to create run")]

    async def apply_run(self, **kwargs: Any) -> List[TextContent]:
        """Apply a planned HCP Terraform run."""
        run_id = kwargs.pop("run_id")
        request = RunActionRequest(**kwargs)
        await self.client.apply_run(run_id, request)
        return [TextContent(type="text", text=f"Successfully applied run {run_id}")]

    async def cancel_run(self, **kwargs: Any) -> List[TextContent]:
        """Cancel a running HCP Terraform run."""
        run_id = kwargs.pop("run_id")
        request = RunActionRequest(**kwargs)
        await self.client.cancel_run(run_id, request)
        return [TextContent(type="text", text=f"Successfully cancelled run {run_id}")]

    async def discard_run(self, **kwargs: Any) -> List[TextContent]:
        """Discard a planned HCP Terraform run."""
        run_id = kwargs.pop("run_id")
        request = RunActionRequest(**kwargs)
        await self.client.discard_run(run_id, request)
        return [TextContent(type="text", text=f"Successfully discarded run {run_id}")]

    async def list_runs(self, **kwargs: Any) -> List[TextContent]:
        """List HCP Terraform runs."""
        response = await self.client.list_runs(**kwargs)
        if response.data:
            runs = response.data if isinstance(response.data, list) else [response.data]
            run_list = []
            for run in runs:
                status = run.attributes.get("status", "Unknown")
                message = run.attributes.get("message", "")
                run_info = f"- Run {run.id}: {status}"
                if message:
                    run_info += f" - {message}"
                run_list.append(run_info)
            runs_text = f"Found {len(runs)} run(s):\n" + "\n".join(run_list)
            return [TextContent(type="text", text=runs_text)]
        return [TextContent(type="text", text="No runs found")]

    async def dispatch(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Dispatch a tool call to the appropriate handler."""
        handler = getattr(self, name, None)
        if handler:
            return await handler(**arguments)
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
