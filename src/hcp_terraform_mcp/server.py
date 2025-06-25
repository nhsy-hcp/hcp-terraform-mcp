"""HCP Terraform MCP Server."""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    EmbeddedResource,
    GetPromptResult,
    ImageContent,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    Prompt,
    PromptMessage,
    ReadResourceResult,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)

from .client import TerraformApiError, TerraformClient
from .config import get_config, validate_environment
from .models import ProjectAttributes, RunAttributes, WorkspaceAttributes

logger = logging.getLogger(__name__)


class TerraformMcpServer:
    """HCP Terraform MCP Server."""

    def __init__(self):
        validate_environment()
        self.config = get_config()
        self.client: Optional[TerraformClient] = None
        self.server = Server("hcp-terraform-mcp")
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes TTL
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def list_tools():
            """List available tools."""
            return [
                Tool(
                    name="health_check",
                    description="Check HCP Terraform API connectivity",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                # Project tools
                Tool(
                    name="create_project",
                    description="Create a new HCP Terraform project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Project name"},
                            "description": {
                                "type": "string",
                                "description": "Project description (optional)",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="update_project",
                    description="Update an existing HCP Terraform project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "Project ID",
                            },
                            "name": {
                                "type": "string",
                                "description": "New project name (optional)",
                            },
                            "description": {
                                "type": "string",
                                "description": "New project description (optional)",
                            },
                        },
                        "required": ["project_id"],
                    },
                ),
                Tool(
                    name="list_projects",
                    description="List HCP Terraform projects in the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include": {
                                "type": "string",
                                "description": "Related resources to include (optional)",
                            },
                            "search": {
                                "type": "string",
                                "description": "Search term to filter projects (optional)",
                            },
                        },
                        "required": [],
                    },
                ),
                # Workspace tools
                Tool(
                    name="create_workspace",
                    description="Create a new HCP Terraform workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Workspace name"},
                            "project_id": {
                                "type": "string",
                                "description": "Project ID to associate with (optional)",
                            },
                            "description": {
                                "type": "string",
                                "description": "Workspace description (optional)",
                            },
                            "auto_apply": {
                                "type": "boolean",
                                "description": "Enable auto-apply (optional)",
                            },
                            "execution_mode": {
                                "type": "string",
                                "description": "Execution mode (local, remote, agent) (optional)",
                            },
                            "terraform_version": {
                                "type": "string",
                                "description": "Terraform version (optional)",
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory (optional)",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="update_workspace",
                    description="Update an existing HCP Terraform workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "Workspace ID",
                            },
                            "name": {
                                "type": "string",
                                "description": "New workspace name (optional)",
                            },
                            "description": {
                                "type": "string",
                                "description": "New workspace description (optional)",
                            },
                            "auto_apply": {
                                "type": "boolean",
                                "description": "Enable auto-apply (optional)",
                            },
                            "execution_mode": {
                                "type": "string",
                                "description": "Execution mode (optional)",
                            },
                            "terraform_version": {
                                "type": "string",
                                "description": "Terraform version (optional)",
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory (optional)",
                            },
                        },
                        "required": ["workspace_id"],
                    },
                ),
                Tool(
                    name="list_workspaces",
                    description="List HCP Terraform workspaces in the organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include": {
                                "type": "string",
                                "description": "Related resources to include (optional)",
                            },
                            "search": {
                                "type": "string",
                                "description": "Search term to filter workspaces (optional)",
                            },
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="lock_workspace",
                    description="Lock an HCP Terraform workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "Workspace ID",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for locking (optional)",
                            },
                        },
                        "required": ["workspace_id"],
                    },
                ),
                Tool(
                    name="unlock_workspace",
                    description="Unlock an HCP Terraform workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "Workspace ID",
                            },
                        },
                        "required": ["workspace_id"],
                    },
                ),
                # Run tools
                Tool(
                    name="create_run",
                    description="Create a new HCP Terraform run",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "Workspace ID",
                            },
                            "message": {
                                "type": "string",
                                "description": "Run message (optional)",
                            },
                            "is_destroy": {
                                "type": "boolean",
                                "description": "Whether this is a destroy run (optional)",
                            },
                            "refresh": {
                                "type": "boolean",
                                "description": "Whether to refresh state (optional)",
                            },
                            "refresh_only": {
                                "type": "boolean",
                                "description": "Whether this is a refresh-only run (optional)",
                            },
                            "plan_only": {
                                "type": "boolean",
                                "description": "Whether this is a plan-only run (optional)",
                            },
                            "replace_addrs": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Resource addresses to replace (optional)",
                            },
                            "target_addrs": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Resource addresses to target (optional)",
                            },
                        },
                        "required": ["workspace_id"],
                    },
                ),
                Tool(
                    name="apply_run",
                    description="Apply a planned HCP Terraform run",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string", "description": "Run ID"},
                            "comment": {
                                "type": "string",
                                "description": "Apply comment (optional)",
                            },
                        },
                        "required": ["run_id"],
                    },
                ),
                Tool(
                    name="cancel_run",
                    description="Cancel a running HCP Terraform run",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string", "description": "Run ID"},
                            "comment": {
                                "type": "string",
                                "description": "Cancel comment (optional)",
                            },
                        },
                        "required": ["run_id"],
                    },
                ),
                Tool(
                    name="discard_run",
                    description="Discard a planned HCP Terraform run",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "run_id": {"type": "string", "description": "Run ID"},
                            "comment": {
                                "type": "string",
                                "description": "Discard comment (optional)",
                            },
                        },
                        "required": ["run_id"],
                    },
                ),
                Tool(
                    name="list_runs",
                    description="List HCP Terraform runs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {
                                "type": "string",
                                "description": "Workspace ID for workspace runs (optional)",
                            },
                            "organization_runs": {
                                "type": "boolean",
                                "description": "List organization-wide runs (optional, default false)",
                            },
                            "include": {
                                "type": "string",
                                "description": "Related resources to include (optional)",
                            },
                            "search": {
                                "type": "string",
                                "description": "Search term to filter runs (optional)",
                            },
                        },
                        "required": [],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """Call a tool."""
            if not self.client:
                return [
                    TextContent(
                        type="text", text="Error: Terraform client not initialized"
                    )
                ]

            try:
                if name == "health_check":
                    is_healthy = await self.client.health_check()
                    status = "healthy" if is_healthy else "unhealthy"
                    return [
                        TextContent(type="text", text=f"HCP Terraform API is {status}")
                    ]

                # Project tools
                elif name == "create_project":
                    project_name = arguments.get("name")
                    description = arguments.get("description")

                    response = await self.client.create_project(
                        project_name, description
                    )

                    if response.data:
                        project_data = response.data
                        return [
                            TextContent(
                                type="text",
                                text=f"Successfully created project '{project_name}' with ID: {project_data.id}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text=f"Failed to create project '{project_name}'",
                            )
                        ]

                elif name == "update_project":
                    project_id = arguments.get("project_id")
                    project_name = arguments.get("name")
                    description = arguments.get("description")

                    response = await self.client.update_project(
                        project_id, project_name, description
                    )

                    if response.data:
                        return [
                            TextContent(
                                type="text",
                                text=f"Successfully updated project {project_id}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text=f"Failed to update project {project_id}",
                            )
                        ]

                elif name == "list_projects":
                    include = arguments.get("include")
                    search = arguments.get("search")

                    response = await self.client.list_projects(include, search)

                    if response.data:
                        projects = (
                            response.data
                            if isinstance(response.data, list)
                            else [response.data]
                        )
                        project_list = []

                        for project in projects:
                            project_info = f"- {project.attributes.get('name', 'Unknown')} (ID: {project.id})"
                            if project.attributes.get("description"):
                                project_info += (
                                    f" - {project.attributes['description']}"
                                )
                            project_list.append(project_info)

                        projects_text = (
                            f"Found {len(projects)} project(s):\n"
                            + "\n".join(project_list)
                        )

                        return [TextContent(type="text", text=projects_text)]
                    else:
                        return [TextContent(type="text", text="No projects found")]

                # Workspace tools
                elif name == "create_workspace":
                    workspace_name = arguments.get("name")
                    project_id = arguments.get("project_id")
                    description = arguments.get("description")
                    auto_apply = arguments.get("auto_apply")
                    execution_mode = arguments.get("execution_mode")
                    terraform_version = arguments.get("terraform_version")
                    working_directory = arguments.get("working_directory")

                    response = await self.client.create_workspace(
                        workspace_name,
                        project_id,
                        description,
                        auto_apply,
                        execution_mode,
                        terraform_version,
                        working_directory,
                    )

                    if response.data:
                        workspace_data = response.data
                        return [
                            TextContent(
                                type="text",
                                text=f"Successfully created workspace '{workspace_name}' with ID: {workspace_data.id}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text=f"Failed to create workspace '{workspace_name}'",
                            )
                        ]

                elif name == "update_workspace":
                    workspace_id = arguments.get("workspace_id")

                    # Build kwargs from all possible update fields
                    update_args = {
                        k: v
                        for k, v in arguments.items()
                        if k != "workspace_id" and v is not None
                    }

                    response = await self.client.update_workspace(
                        workspace_id, **update_args
                    )

                    if response.data:
                        return [
                            TextContent(
                                type="text",
                                text=f"Successfully updated workspace {workspace_id}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text=f"Failed to update workspace {workspace_id}",
                            )
                        ]

                elif name == "list_workspaces":
                    include = arguments.get("include")
                    search = arguments.get("search")

                    response = await self.client.list_workspaces(include, search)

                    if response.data:
                        workspaces = (
                            response.data
                            if isinstance(response.data, list)
                            else [response.data]
                        )
                        workspace_list = []

                        for workspace in workspaces:
                            workspace_info = f"- {workspace.attributes.get('name', 'Unknown')} (ID: {workspace.id})"
                            if workspace.attributes.get("description"):
                                workspace_info += (
                                    f" - {workspace.attributes['description']}"
                                )
                            if workspace.attributes.get("locked"):
                                workspace_info += " [LOCKED]"
                            workspace_list.append(workspace_info)

                        workspaces_text = (
                            f"Found {len(workspaces)} workspace(s):\n"
                            + "\n".join(workspace_list)
                        )

                        return [TextContent(type="text", text=workspaces_text)]
                    else:
                        return [TextContent(type="text", text="No workspaces found")]

                elif name == "lock_workspace":
                    workspace_id = arguments.get("workspace_id")
                    reason = arguments.get("reason")

                    response = await self.client.lock_workspace(workspace_id, reason)

                    if response.data:
                        return [
                            TextContent(
                                type="text",
                                text=f"Successfully locked workspace {workspace_id}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text=f"Failed to lock workspace {workspace_id}",
                            )
                        ]

                elif name == "unlock_workspace":
                    workspace_id = arguments.get("workspace_id")

                    response = await self.client.unlock_workspace(workspace_id)

                    if response.data:
                        return [
                            TextContent(
                                type="text",
                                text=f"Successfully unlocked workspace {workspace_id}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text=f"Failed to unlock workspace {workspace_id}",
                            )
                        ]

                # Run tools
                elif name == "create_run":
                    workspace_id = arguments.get("workspace_id")
                    message = arguments.get("message")
                    is_destroy = arguments.get("is_destroy")
                    refresh = arguments.get("refresh")
                    refresh_only = arguments.get("refresh_only")
                    plan_only = arguments.get("plan_only")
                    replace_addrs = arguments.get("replace_addrs")
                    target_addrs = arguments.get("target_addrs")

                    response = await self.client.create_run(
                        workspace_id,
                        message,
                        is_destroy,
                        refresh,
                        refresh_only,
                        replace_addrs,
                        target_addrs,
                        plan_only,
                    )

                    if response.data:
                        run_data = response.data
                        return [
                            TextContent(
                                type="text",
                                text=f"Successfully created run with ID: {run_data.id}",
                            )
                        ]
                    else:
                        return [TextContent(type="text", text="Failed to create run")]

                elif name == "apply_run":
                    run_id = arguments.get("run_id")
                    comment = arguments.get("comment")

                    response = await self.client.apply_run(run_id, comment)

                    if response.data:
                        return [
                            TextContent(
                                type="text", text=f"Successfully applied run {run_id}"
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text", text=f"Failed to apply run {run_id}"
                            )
                        ]

                elif name == "cancel_run":
                    run_id = arguments.get("run_id")
                    comment = arguments.get("comment")

                    response = await self.client.cancel_run(run_id, comment)

                    if response.data:
                        return [
                            TextContent(
                                type="text", text=f"Successfully cancelled run {run_id}"
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text", text=f"Failed to cancel run {run_id}"
                            )
                        ]

                elif name == "discard_run":
                    run_id = arguments.get("run_id")
                    comment = arguments.get("comment")

                    response = await self.client.discard_run(run_id, comment)

                    if response.data:
                        return [
                            TextContent(
                                type="text", text=f"Successfully discarded run {run_id}"
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text", text=f"Failed to discard run {run_id}"
                            )
                        ]

                elif name == "list_runs":
                    workspace_id = arguments.get("workspace_id")
                    organization_runs = arguments.get("organization_runs", False)
                    include = arguments.get("include")
                    search = arguments.get("search")

                    response = await self.client.list_runs(
                        workspace_id, organization_runs, include, search
                    )

                    if response.data:
                        runs = (
                            response.data
                            if isinstance(response.data, list)
                            else [response.data]
                        )
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
                    else:
                        return [TextContent(type="text", text="No runs found")]

                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except TerraformApiError as e:
                return [TextContent(type="text", text=f"API Error: {str(e)}")]
            except Exception as e:
                logger.exception("Unexpected error in tool call")
                return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]

        @self.server.list_resources()
        async def list_resources():
            """List available resources."""
            resources = [
                Resource(
                    uri="terraform://organization/info",
                    name="Organization Information",
                    description="Basic information about the HCP Terraform organization",
                    mimeType="application/json",
                ),
            ]

            # Add dynamic resources if client is available
            if self.client:
                try:
                    # Add project resources
                    projects_response = await self.client.list_projects()
                    if projects_response.data:
                        projects = (
                            projects_response.data
                            if isinstance(projects_response.data, list)
                            else [projects_response.data]
                        )
                        for project in projects:
                            resources.append(
                                Resource(
                                    uri=f"terraform://project/{project.id}",
                                    name=f"Project: {project.attributes.get('name', 'Unknown')}",
                                    description=f"Details for project {project.id}",
                                    mimeType="application/json",
                                )
                            )

                    # Add workspace resources
                    workspaces_response = await self.client.list_workspaces()
                    if workspaces_response.data:
                        workspaces = (
                            workspaces_response.data
                            if isinstance(workspaces_response.data, list)
                            else [workspaces_response.data]
                        )
                        for workspace in workspaces:
                            resources.append(
                                Resource(
                                    uri=f"terraform://workspace/{workspace.id}",
                                    name=f"Workspace: {workspace.attributes.get('name', 'Unknown')}",
                                    description=f"Details for workspace {workspace.id}",
                                    mimeType="application/json",
                                )
                            )

                    # Add recent runs
                    runs_response = await self.client.list_runs(organization_runs=True)
                    if runs_response.data:
                        runs = (
                            runs_response.data
                            if isinstance(runs_response.data, list)
                            else [runs_response.data]
                        )
                        for run in runs[:10]:  # Limit to 10 most recent runs
                            status = run.attributes.get("status", "Unknown")
                            resources.append(
                                Resource(
                                    uri=f"terraform://run/{run.id}",
                                    name=f"Run: {run.id} ({status})",
                                    description=f"Details for run {run.id}",
                                    mimeType="application/json",
                                )
                            )

                except Exception as e:
                    logger.warning(f"Error fetching dynamic resources: {e}")

            return resources

        @self.server.read_resource()
        async def read_resource(uri: str):
            """Read a resource."""
            if not self.client:
                return {
                    "contents": [
                        TextResourceContents(
                            uri=uri,
                            text="Error: Terraform client not initialized",
                            mimeType="text/plain",
                        )
                    ]
                }

            try:
                # Check cache first
                cache_key = f"resource_{uri}"
                cached_data = self._get_from_cache(cache_key)
                if cached_data:
                    return {
                        "contents": [
                            TextResourceContents(
                                uri=uri, text=cached_data, mimeType="application/json"
                            )
                        ]
                    }

                if uri == "terraform://organization/info":
                    # Get organization info
                    response = await self.client.get(
                        self.client.get_organization_endpoint()
                    )

                    if response.data:
                        org_info = {
                            "name": self.config.organization,
                            "api_url": self.config.base_url,
                            "status": "connected",
                            "retrieved_at": time.time(),
                        }

                        org_info_json = json.dumps(org_info, indent=2)
                        self._set_cache(cache_key, org_info_json)

                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri,
                                    text=org_info_json,
                                    mimeType="application/json",
                                )
                            ]
                        }
                    else:
                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri,
                                    text="No organization data found",
                                    mimeType="text/plain",
                                )
                            ]
                        }

                elif uri.startswith("terraform://project/"):
                    project_id = uri.split("/")[-1]
                    response = await self.client.get_project(project_id)

                    if response.data:
                        # Validate with Pydantic model
                        try:
                            project_attrs = ProjectAttributes(
                                **response.data.attributes
                            )
                            project_data = {
                                "id": response.data.id,
                                "type": response.data.type,
                                "attributes": project_attrs.model_dump(),
                                "retrieved_at": time.time(),
                            }
                        except Exception as e:
                            logger.warning(f"Project validation failed: {e}")
                            project_data = {
                                "id": response.data.id,
                                "type": response.data.type,
                                "attributes": response.data.attributes,
                                "retrieved_at": time.time(),
                                "validation_error": str(e),
                            }

                        project_json = json.dumps(project_data, indent=2, default=str)
                        self._set_cache(cache_key, project_json)

                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri,
                                    text=project_json,
                                    mimeType="application/json",
                                )
                            ]
                        }
                    else:
                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri,
                                    text=f"Project {project_id} not found",
                                    mimeType="text/plain",
                                )
                            ]
                        }

                elif uri.startswith("terraform://workspace/"):
                    workspace_id = uri.split("/")[-1]
                    response = await self.client.get_workspace(workspace_id)

                    if response.data:
                        # Validate with Pydantic model
                        try:
                            workspace_attrs = WorkspaceAttributes(
                                **response.data.attributes
                            )
                            workspace_data = {
                                "id": response.data.id,
                                "type": response.data.type,
                                "attributes": workspace_attrs.model_dump(),
                                "retrieved_at": time.time(),
                            }
                        except Exception as e:
                            logger.warning(f"Workspace validation failed: {e}")
                            workspace_data = {
                                "id": response.data.id,
                                "type": response.data.type,
                                "attributes": response.data.attributes,
                                "retrieved_at": time.time(),
                                "validation_error": str(e),
                            }

                        workspace_json = json.dumps(
                            workspace_data, indent=2, default=str
                        )
                        self._set_cache(cache_key, workspace_json)

                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri,
                                    text=workspace_json,
                                    mimeType="application/json",
                                )
                            ]
                        }
                    else:
                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri,
                                    text=f"Workspace {workspace_id} not found",
                                    mimeType="text/plain",
                                )
                            ]
                        }

                elif uri.startswith("terraform://run/"):
                    run_id = uri.split("/")[-1]
                    response = await self.client.get_run(run_id)

                    if response.data:
                        # Validate with Pydantic model
                        try:
                            run_attrs = RunAttributes(**response.data.attributes)
                            run_data = {
                                "id": response.data.id,
                                "type": response.data.type,
                                "attributes": run_attrs.model_dump(),
                                "retrieved_at": time.time(),
                            }
                        except Exception as e:
                            logger.warning(f"Run validation failed: {e}")
                            run_data = {
                                "id": response.data.id,
                                "type": response.data.type,
                                "attributes": response.data.attributes,
                                "retrieved_at": time.time(),
                                "validation_error": str(e),
                            }

                        run_json = json.dumps(run_data, indent=2, default=str)
                        self._set_cache(cache_key, run_json)

                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri, text=run_json, mimeType="application/json"
                                )
                            ]
                        }
                    else:
                        return {
                            "contents": [
                                TextResourceContents(
                                    uri=uri,
                                    text=f"Run {run_id} not found",
                                    mimeType="text/plain",
                                )
                            ]
                        }
                else:
                    return {
                        "contents": [
                            TextResourceContents(
                                uri=uri,
                                text=f"Unknown resource: {uri}",
                                mimeType="text/plain",
                            )
                        ]
                    }

            except TerraformApiError as e:
                return {
                    "contents": [
                        TextResourceContents(
                            uri=uri, text=f"API Error: {str(e)}", mimeType="text/plain"
                        )
                    ]
                }
            except Exception as e:
                logger.exception("Unexpected error in resource read")
                return {
                    "contents": [
                        TextResourceContents(
                            uri=uri,
                            text=f"Unexpected error: {str(e)}",
                            mimeType="text/plain",
                        )
                    ]
                }

        @self.server.list_prompts()
        async def list_prompts():
            """List available prompts."""
            return [
                Prompt(
                    name="terraform_status",
                    description="Get the current status of HCP Terraform organization",
                    arguments=[],
                ),
                Prompt(
                    name="terraform_deployment",
                    description="Plan and execute a Terraform deployment",
                    arguments=[
                        {
                            "name": "workspace_name",
                            "description": "Name of the workspace to deploy",
                            "required": True,
                        },
                        {
                            "name": "message",
                            "description": "Deployment message",
                            "required": False,
                        },
                        {
                            "name": "auto_apply",
                            "description": "Whether to auto-apply the plan",
                            "required": False,
                        },
                    ],
                ),
                Prompt(
                    name="workspace_setup",
                    description="Set up a new Terraform workspace",
                    arguments=[
                        {
                            "name": "workspace_name",
                            "description": "Name for the new workspace",
                            "required": True,
                        },
                        {
                            "name": "project_name",
                            "description": "Name of the project (optional)",
                            "required": False,
                        },
                        {
                            "name": "terraform_version",
                            "description": "Terraform version to use",
                            "required": False,
                        },
                    ],
                ),
                Prompt(
                    name="run_monitoring",
                    description="Monitor the status of Terraform runs",
                    arguments=[
                        {
                            "name": "workspace_name",
                            "description": "Name of the workspace to monitor",
                            "required": False,
                        },
                        {
                            "name": "run_id",
                            "description": "Specific run ID to monitor",
                            "required": False,
                        },
                    ],
                ),
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """Get a prompt."""
            if name == "terraform_status":
                return GetPromptResult(
                    description="Check HCP Terraform organization status",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text="Please check the status of my HCP Terraform organization and provide a summary of the current state, including recent runs and workspace statuses.",
                            ),
                        )
                    ],
                )
            elif name == "terraform_deployment":
                workspace_name = arguments.get("workspace_name", "[WORKSPACE_NAME]")
                message = arguments.get("message", "Deployment via MCP")
                auto_apply = arguments.get("auto_apply", "false").lower() == "true"

                prompt_text = f"""I want to deploy changes to the '{workspace_name}' workspace. 
                
Please:
1. Check the current status of the workspace
2. Create a new run with the message: "{message}"
3. {'Automatically apply the run if the plan is successful' if auto_apply else 'Show me the plan and wait for confirmation before applying'}
4. Monitor the run status and provide updates

Make sure to handle any errors gracefully and provide clear status updates throughout the process."""

                return GetPromptResult(
                    description="Plan and execute a Terraform deployment",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=prompt_text),
                        )
                    ],
                )
            elif name == "workspace_setup":
                workspace_name = arguments.get("workspace_name", "[WORKSPACE_NAME]")
                project_name = arguments.get("project_name", "")
                terraform_version = arguments.get("terraform_version", "latest")

                prompt_text = f"""I want to set up a new Terraform workspace named '{workspace_name}'.
                
Please:
1. {'Create a new project named "' + project_name + '" first, then ' if project_name else ''}Create the workspace with the following settings:
   - Name: {workspace_name}
   - Terraform version: {terraform_version}
   - Execution mode: remote
   - Auto-apply: disabled (for safety)
2. Verify the workspace was created successfully
3. Show me the workspace configuration
4. Provide guidance on next steps for connecting VCS and configuring variables

Make sure to follow security best practices and provide clear instructions for the setup process."""

                return GetPromptResult(
                    description="Set up a new Terraform workspace",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=prompt_text),
                        )
                    ],
                )
            elif name == "run_monitoring":
                workspace_name = arguments.get("workspace_name", "")
                run_id = arguments.get("run_id", "")

                if run_id:
                    prompt_text = f"""Please monitor the status of run '{run_id}' and provide regular updates.
                    
I want to:
1. Check the current status of the run
2. Show me the run details (plan, apply status, etc.)
3. If the run is waiting for confirmation, let me know
4. Provide updates on the progress
5. Alert me if there are any errors or issues

Keep monitoring until the run is complete or encounters an error."""
                elif workspace_name:
                    prompt_text = f"""Please monitor the recent runs for workspace '{workspace_name}' and provide a status summary.
                    
I want to:
1. List the recent runs for this workspace
2. Show the status of each run
3. Highlight any failed or pending runs
4. Provide details on the most recent run
5. Alert me to any issues that need attention

Focus on runs from the last 24 hours and provide actionable insights."""
                else:
                    prompt_text = """Please provide an overview of all recent Terraform runs across the organization.
                    
I want to:
1. List recent runs across all workspaces
2. Identify any failed or stuck runs
3. Show summary statistics (success rate, average duration, etc.)
4. Highlight any runs that need immediate attention
5. Provide recommendations for improving run reliability

Focus on the most critical issues and provide actionable insights."""

                return GetPromptResult(
                    description="Monitor the status of Terraform runs",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=prompt_text),
                        )
                    ],
                )
            else:
                return GetPromptResult(
                    description=f"Unknown prompt: {name}",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text", text=f"Error: Unknown prompt '{name}'"
                            ),
                        )
                    ],
                )

    async def start(self):
        """Start the MCP server."""
        try:
            self.client = TerraformClient(self.config)
            logger.info("Starting HCP Terraform MCP Server")

            # Test connection
            if await self.client.health_check():
                logger.info("Successfully connected to HCP Terraform API")
            else:
                logger.warning("Failed to connect to HCP Terraform API")

        except Exception as e:
            logger.error(f"Failed to initialize Terraform client: {e}")
            raise

    async def stop(self):
        """Stop the MCP server."""
        if self.client:
            await self.client.close()
        logger.info("HCP Terraform MCP Server stopped")

    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get cached data if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                # Remove expired cache entry
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: str) -> None:
        """Set cache data with current timestamp."""
        self._cache[key] = (data, time.time())

    def _clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def run(self):
        """Run the MCP server."""

        async def main():
            async with stdio_server() as streams:
                await self.start()
                try:
                    await self.server.run(
                        streams[0],
                        streams[1],
                        self.server.create_initialization_options(),
                    )
                finally:
                    await self.stop()

        import asyncio

        asyncio.run(main())


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    server = TerraformMcpServer()
    server.run()


if __name__ == "__main__":
    main()
