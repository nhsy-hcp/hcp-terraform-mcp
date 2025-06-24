"""HCP Terraform MCP Server."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    TextResourceContents,
    ImageContent,
    EmbeddedResource,
    Prompt,
    GetPromptResult,
    PromptMessage,
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    ListPromptsResult,
    ReadResourceResult,
)

from .client import TerraformClient, TerraformApiError
from .config import get_config


logger = logging.getLogger(__name__)


class TerraformMcpServer:
    """HCP Terraform MCP Server."""
    
    def __init__(self):
        self.config = get_config()
        self.client: Optional[TerraformClient] = None
        self.server = Server("hcp-terraform-mcp")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(
                tools=[
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
                                "description": {"type": "string", "description": "Project description (optional)"},
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
                                "project_id": {"type": "string", "description": "Project ID"},
                                "name": {"type": "string", "description": "New project name (optional)"},
                                "description": {"type": "string", "description": "New project description (optional)"},
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
                                "include": {"type": "string", "description": "Related resources to include (optional)"},
                                "search": {"type": "string", "description": "Search term to filter projects (optional)"},
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
                                "project_id": {"type": "string", "description": "Project ID to associate with (optional)"},
                                "description": {"type": "string", "description": "Workspace description (optional)"},
                                "auto_apply": {"type": "boolean", "description": "Enable auto-apply (optional)"},
                                "execution_mode": {"type": "string", "description": "Execution mode (local, remote, agent) (optional)"},
                                "terraform_version": {"type": "string", "description": "Terraform version (optional)"},
                                "working_directory": {"type": "string", "description": "Working directory (optional)"},
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
                                "workspace_id": {"type": "string", "description": "Workspace ID"},
                                "name": {"type": "string", "description": "New workspace name (optional)"},
                                "description": {"type": "string", "description": "New workspace description (optional)"},
                                "auto_apply": {"type": "boolean", "description": "Enable auto-apply (optional)"},
                                "execution_mode": {"type": "string", "description": "Execution mode (optional)"},
                                "terraform_version": {"type": "string", "description": "Terraform version (optional)"},
                                "working_directory": {"type": "string", "description": "Working directory (optional)"},
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
                                "include": {"type": "string", "description": "Related resources to include (optional)"},
                                "search": {"type": "string", "description": "Search term to filter workspaces (optional)"},
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
                                "workspace_id": {"type": "string", "description": "Workspace ID"},
                                "reason": {"type": "string", "description": "Reason for locking (optional)"},
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
                                "workspace_id": {"type": "string", "description": "Workspace ID"},
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
                                "workspace_id": {"type": "string", "description": "Workspace ID"},
                                "message": {"type": "string", "description": "Run message (optional)"},
                                "is_destroy": {"type": "boolean", "description": "Whether this is a destroy run (optional)"},
                                "refresh": {"type": "boolean", "description": "Whether to refresh state (optional)"},
                                "refresh_only": {"type": "boolean", "description": "Whether this is a refresh-only run (optional)"},
                                "plan_only": {"type": "boolean", "description": "Whether this is a plan-only run (optional)"},
                                "replace_addrs": {"type": "array", "items": {"type": "string"}, "description": "Resource addresses to replace (optional)"},
                                "target_addrs": {"type": "array", "items": {"type": "string"}, "description": "Resource addresses to target (optional)"},
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
                                "comment": {"type": "string", "description": "Apply comment (optional)"},
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
                                "comment": {"type": "string", "description": "Cancel comment (optional)"},
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
                                "comment": {"type": "string", "description": "Discard comment (optional)"},
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
                                "workspace_id": {"type": "string", "description": "Workspace ID for workspace runs (optional)"},
                                "organization_runs": {"type": "boolean", "description": "List organization-wide runs (optional, default false)"},
                                "include": {"type": "string", "description": "Related resources to include (optional)"},
                                "search": {"type": "string", "description": "Search term to filter runs (optional)"},
                            },
                            "required": [],
                        },
                    ),
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Call a tool."""
            if not self.client:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Terraform client not initialized"
                        )
                    ]
                )
            
            try:
                if name == "health_check":
                    is_healthy = await self.client.health_check()
                    status = "healthy" if is_healthy else "unhealthy"
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"HCP Terraform API is {status}"
                            )
                        ]
                    )
                
                # Project tools
                elif name == "create_project":
                    project_name = arguments.get("name")
                    description = arguments.get("description")
                    
                    response = await self.client.create_project(project_name, description)
                    
                    if response.data:
                        project_data = response.data
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully created project '{project_name}' with ID: {project_data.id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to create project '{project_name}'"
                                )
                            ]
                        )
                
                elif name == "update_project":
                    project_id = arguments.get("project_id")
                    project_name = arguments.get("name")
                    description = arguments.get("description")
                    
                    response = await self.client.update_project(project_id, project_name, description)
                    
                    if response.data:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully updated project {project_id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to update project {project_id}"
                                )
                            ]
                        )
                
                elif name == "list_projects":
                    include = arguments.get("include")
                    search = arguments.get("search")
                    
                    response = await self.client.list_projects(include, search)
                    
                    if response.data:
                        projects = response.data if isinstance(response.data, list) else [response.data]
                        project_list = []
                        
                        for project in projects:
                            project_info = f"- {project.attributes.get('name', 'Unknown')} (ID: {project.id})"
                            if project.attributes.get('description'):
                                project_info += f" - {project.attributes['description']}"
                            project_list.append(project_info)
                        
                        projects_text = f"Found {len(projects)} project(s):\n" + "\n".join(project_list)
                        
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=projects_text
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text="No projects found"
                                )
                            ]
                        )
                
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
                        workspace_name, project_id, description, auto_apply,
                        execution_mode, terraform_version, working_directory
                    )
                    
                    if response.data:
                        workspace_data = response.data
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully created workspace '{workspace_name}' with ID: {workspace_data.id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to create workspace '{workspace_name}'"
                                )
                            ]
                        )
                
                elif name == "update_workspace":
                    workspace_id = arguments.get("workspace_id")
                    
                    # Build kwargs from all possible update fields
                    update_args = {
                        k: v for k, v in arguments.items() 
                        if k != "workspace_id" and v is not None
                    }
                    
                    response = await self.client.update_workspace(workspace_id, **update_args)
                    
                    if response.data:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully updated workspace {workspace_id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to update workspace {workspace_id}"
                                )
                            ]
                        )
                
                elif name == "list_workspaces":
                    include = arguments.get("include")
                    search = arguments.get("search")
                    
                    response = await self.client.list_workspaces(include, search)
                    
                    if response.data:
                        workspaces = response.data if isinstance(response.data, list) else [response.data]
                        workspace_list = []
                        
                        for workspace in workspaces:
                            workspace_info = f"- {workspace.attributes.get('name', 'Unknown')} (ID: {workspace.id})"
                            if workspace.attributes.get('description'):
                                workspace_info += f" - {workspace.attributes['description']}"
                            if workspace.attributes.get('locked'):
                                workspace_info += " [LOCKED]"
                            workspace_list.append(workspace_info)
                        
                        workspaces_text = f"Found {len(workspaces)} workspace(s):\n" + "\n".join(workspace_list)
                        
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=workspaces_text
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text="No workspaces found"
                                )
                            ]
                        )
                
                elif name == "lock_workspace":
                    workspace_id = arguments.get("workspace_id")
                    reason = arguments.get("reason")
                    
                    response = await self.client.lock_workspace(workspace_id, reason)
                    
                    if response.data:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully locked workspace {workspace_id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to lock workspace {workspace_id}"
                                )
                            ]
                        )
                
                elif name == "unlock_workspace":
                    workspace_id = arguments.get("workspace_id")
                    
                    response = await self.client.unlock_workspace(workspace_id)
                    
                    if response.data:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully unlocked workspace {workspace_id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to unlock workspace {workspace_id}"
                                )
                            ]
                        )
                
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
                        workspace_id, message, is_destroy, refresh, refresh_only,
                        replace_addrs, target_addrs, plan_only
                    )
                    
                    if response.data:
                        run_data = response.data
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully created run with ID: {run_data.id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text="Failed to create run"
                                )
                            ]
                        )
                
                elif name == "apply_run":
                    run_id = arguments.get("run_id")
                    comment = arguments.get("comment")
                    
                    response = await self.client.apply_run(run_id, comment)
                    
                    if response.data:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully applied run {run_id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to apply run {run_id}"
                                )
                            ]
                        )
                
                elif name == "cancel_run":
                    run_id = arguments.get("run_id")
                    comment = arguments.get("comment")
                    
                    response = await self.client.cancel_run(run_id, comment)
                    
                    if response.data:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully cancelled run {run_id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to cancel run {run_id}"
                                )
                            ]
                        )
                
                elif name == "discard_run":
                    run_id = arguments.get("run_id")
                    comment = arguments.get("comment")
                    
                    response = await self.client.discard_run(run_id, comment)
                    
                    if response.data:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully discarded run {run_id}"
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Failed to discard run {run_id}"
                                )
                            ]
                        )
                
                elif name == "list_runs":
                    workspace_id = arguments.get("workspace_id")
                    organization_runs = arguments.get("organization_runs", False)
                    include = arguments.get("include")
                    search = arguments.get("search")
                    
                    response = await self.client.list_runs(workspace_id, organization_runs, include, search)
                    
                    if response.data:
                        runs = response.data if isinstance(response.data, list) else [response.data]
                        run_list = []
                        
                        for run in runs:
                            status = run.attributes.get('status', 'Unknown')
                            message = run.attributes.get('message', '')
                            run_info = f"- Run {run.id}: {status}"
                            if message:
                                run_info += f" - {message}"
                            run_list.append(run_info)
                        
                        runs_text = f"Found {len(runs)} run(s):\n" + "\n".join(run_list)
                        
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=runs_text
                                )
                            ]
                        )
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text="No runs found"
                                )
                            ]
                        )
                
                else:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Unknown tool: {name}"
                            )
                        ]
                    )
            
            except TerraformApiError as e:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"API Error: {str(e)}"
                        )
                    ]
                )
            except Exception as e:
                logger.exception("Unexpected error in tool call")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Unexpected error: {str(e)}"
                        )
                    ]
                )
        
        @self.server.list_resources()
        async def list_resources():
            """List available resources."""
            return [
                Resource(
                    uri="terraform://organization/info",
                    name="Organization Information",
                    description="Basic information about the HCP Terraform organization",
                    mimeType="application/json",
                ),
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read a resource."""
            if not self.client:
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=uri,
                            text="Error: Terraform client not initialized",
                            mimeType="text/plain"
                        )
                    ]
                )
            
            try:
                if uri == "terraform://organization/info":
                    # Get organization info
                    response = await self.client.get(
                        self.client.get_organization_endpoint()
                    )
                    
                    if response.data:
                        org_info = {
                            "name": self.config.organization,
                            "api_url": self.config.base_url,
                            "status": "connected"
                        }
                        
                        return ReadResourceResult(
                            contents=[
                                TextResourceContents(
                                    uri=uri,
                                    text=str(org_info),
                                    mimeType="application/json"
                                )
                            ]
                        )
                    else:
                        return ReadResourceResult(
                            contents=[
                                TextResourceContents(
                                    uri=uri,
                                    text="No organization data found",
                                    mimeType="text/plain"
                                )
                            ]
                        )
                else:
                    return ReadResourceResult(
                        contents=[
                            TextResourceContents(
                                uri=uri,
                                text=f"Unknown resource: {uri}",
                                mimeType="text/plain"
                            )
                        ]
                    )
            
            except TerraformApiError as e:
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=uri,
                            text=f"API Error: {str(e)}",
                            mimeType="text/plain"
                        )
                    ]
                )
            except Exception as e:
                logger.exception("Unexpected error in resource read")
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=uri,
                            text=f"Unexpected error: {str(e)}",
                            mimeType="text/plain"
                        )
                    ]
                )
        
        @self.server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List available prompts."""
            return ListPromptsResult(
                prompts=[
                    Prompt(
                        name="terraform_status",
                        description="Get the current status of HCP Terraform organization",
                        arguments=[],
                    ),
                ]
            )
        
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
                                text="Please check the status of my HCP Terraform organization and provide a summary of the current state."
                            ),
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
                                type="text",
                                text=f"Error: Unknown prompt '{name}'"
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
    
    def run(self):
        """Run the MCP server."""
        async def main():
            async with stdio_server() as streams:
                await self.start()
                try:
                    await self.server.run(
                        streams[0], streams[1], self.server.create_initialization_options()
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