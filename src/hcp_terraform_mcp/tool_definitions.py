"""Tool definitions for the HCP Terraform MCP Server."""

from mcp.types import Tool


def get_tools():
    """Returns a list of all available tools."""
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
