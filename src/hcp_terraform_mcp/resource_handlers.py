"""Resource handlers for the HCP Terraform MCP Server."""

import json
import logging
import time
from typing import Any, List

from mcp.types import AnyUrl, Resource, ReadResourceResult, TextResourceContents

from .client import TerraformClient, TerraformApiError
from .config import TerraformConfig

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
        ]

        try:
            # Add project resources
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

        return resources

    async def read_resource(self, uri: AnyUrl) -> Any:
        """Read a single resource by its URI."""
        uri_str = str(uri)
        if self.config.debug_mode:
            logger.debug(f"Reading resource: {uri_str}")

        try:
            if uri_str == "terraform://organization/info":
                response = await self.client.get(
                    self.client.endpoints.organization_details()
                )
                if response.data:
                    org_info = {
                        "name": self.config.organization,
                        "api_url": self.config.base_url,
                        "status": "connected",
                        "retrieved_at": time.time(),
                        "data": response.data.attributes,
                    }
                    return json.dumps(org_info, indent=2)
            elif uri_str.startswith("terraform://project/"):
                project_id = uri_str.split("/")[-1]
                response = await self.client.get_project(project_id)
                if response.data:
                    return response.data.model_dump_json(indent=2)

            return ReadResourceResult(
                contents=[
                    TextResourceContents(
                        uri=uri,
                        text=f"Unknown or empty resource: {uri_str}",
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
