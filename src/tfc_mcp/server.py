"""HCP Terraform MCP Server."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
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
        self.server = Server("terraform-mcp")
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
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="terraform://organization/info",
                        name="Organization Information",
                        description="Basic information about the HCP Terraform organization",
                        mimeType="application/json",
                    ),
                ]
            )
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read a resource."""
            if not self.client:
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text="Error: Terraform client not initialized"
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
                                TextContent(
                                    type="text",
                                    text=str(org_info)
                                )
                            ]
                        )
                    else:
                        return ReadResourceResult(
                            contents=[
                                TextContent(
                                    type="text",
                                    text="No organization data found"
                                )
                            ]
                        )
                else:
                    return ReadResourceResult(
                        contents=[
                            TextContent(
                                type="text",
                                text=f"Unknown resource: {uri}"
                            )
                        ]
                    )
            
            except TerraformApiError as e:
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"API Error: {str(e)}"
                        )
                    ]
                )
            except Exception as e:
                logger.exception("Unexpected error in resource read")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"Unexpected error: {str(e)}"
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