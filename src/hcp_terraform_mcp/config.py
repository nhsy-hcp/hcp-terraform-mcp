"""Configuration management for HCP Terraform MCP Server."""

import os
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TerraformConfig(BaseSettings):
    """Configuration for HCP Terraform API."""
    
    model_config = SettingsConfigDict(env_prefix="TFC_", env_file=".env")
    
    api_token: str = Field(..., description="HCP Terraform API token")
    organization: str = Field(..., description="Organization name")
    base_url: str = Field(
        default="https://app.terraform.io/api/v2",
        description="Base URL for HCP Terraform API"
    )


def get_config() -> TerraformConfig:
    """Get configuration from environment variables."""
    return TerraformConfig()