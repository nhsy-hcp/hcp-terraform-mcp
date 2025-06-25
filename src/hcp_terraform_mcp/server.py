"""HCP Terraform MCP Server."""

import asyncio
import logging
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import GetPromptResult, Prompt, PromptMessage, TextContent

from .client import TerraformApiError, TerraformClient
from .config import get_config
from .resource_handlers import ResourceHandler
from .tool_definitions import get_tools
from .tool_handlers import ToolHandlers

logger = logging.getLogger(__name__)

server = Server("hcp-terraform-mcp")
config = get_config()
client: Optional[TerraformClient] = None
tool_handlers: Optional[ToolHandlers] = None
resource_handler: Optional[ResourceHandler] = None

if config.debug_mode:
    logger.setLevel(logging.DEBUG)


def _get_safe_config_for_logging() -> dict:
    """Get configuration with sensitive data obfuscated for logging."""
    config_dict = config.model_dump()
    if config_dict.get("api_token"):
        token = config_dict["api_token"]
        config_dict["api_token"] = (
            f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "****"
        )
    return config_dict


@server.list_tools()
async def list_tools():
    """List available tools."""
    return get_tools()


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    """Call a tool."""
    if not tool_handlers:
        return [TextContent(type="text", text="Error: Tool handlers not initialized")]
    try:
        return await tool_handlers.dispatch(name, arguments)
    except TerraformApiError as e:
        return [TextContent(type="text", text=f"API Error: {e}")]
    except Exception as e:
        logger.exception("Unexpected error in tool call")
        return [TextContent(type="text", text=f"Unexpected error: {e}")]


@server.list_resources()
async def list_resources():
    """List available resources."""
    if not resource_handler:
        return []
    return await resource_handler.list_resources()


@server.read_resource()
async def read_resource(uri: str) -> Any:
    """Read a resource."""
    if not resource_handler:
        return TextContent(type="text", text="Error: Resource handler not initialized")
    return await resource_handler.read_resource(uri)


@server.list_prompts()
async def list_prompts():
    """List available prompts."""
    return [
        Prompt(
            name="terraform_status",
            description="Get the current status of HCP Terraform organization",
            arguments=[],
        ),
    ]


@server.get_prompt()
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


async def start_server():
    """Start the MCP server."""
    global client, tool_handlers, resource_handler
    try:
        client = TerraformClient(config)
        tool_handlers = ToolHandlers(client)
        resource_handler = ResourceHandler(client, config)
        logger.info("Starting HCP Terraform MCP Server")

        if config.debug_mode:
            logger.debug(f"Server configuration: {_get_safe_config_for_logging()}")

        if await client.health_check():
            logger.info("Successfully connected to HCP Terraform API")
        else:
            logger.warning("Failed to connect to HCP Terraform API")

    except Exception as e:
        logger.error(f"Failed to initialize Terraform client: {e}")
        raise


async def stop_server():
    """Stop the MCP server."""
    if client:
        await client.close()
    logger.info("HCP Terraform MCP Server stopped")


def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def run():
        async with stdio_server() as streams:
            await start_server()
            try:
                await server.run(
                    streams[0],
                    streams[1],
                    server.create_initialization_options(),
                )
            finally:
                await stop_server()

    asyncio.run(run())


if __name__ == "__main__":
    main()
