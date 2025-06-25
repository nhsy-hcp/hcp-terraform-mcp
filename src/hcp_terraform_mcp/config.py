"""Configuration management for HCP Terraform MCP Server."""

import os
from typing import Optional

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Configuration validation error."""

    pass


class TerraformConfig(BaseSettings):
    """Configuration for HCP Terraform API."""

    model_config = SettingsConfigDict(env_prefix="TFC_", env_file=".env")

    api_token: str = Field(..., description="HCP Terraform API token")
    organization: str = Field(..., description="Organization name")
    base_url: str = Field(
        default="https://app.terraform.io/api/v2",
        description="Base URL for HCP Terraform API",
    )
    enable_caching: bool = Field(
        default=False, description="Enable resource caching (default: False)"
    )
    debug_mode: bool = Field(
        default=False, description="Enable debug logging (default: False)"
    )


def get_config() -> TerraformConfig:
    """Get configuration from environment variables."""
    try:
        return TerraformConfig()
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed: {e}")


def validate_environment() -> None:
    """Validate required environment variables are set."""
    required_vars = {
        "TFC_API_TOKEN": "HCP Terraform API token is required",
        "TFC_ORGANIZATION": "HCP Terraform organization name is required",
    }

    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"- {var}: {description}")

    if missing_vars:
        error_msg = "Missing required environment variables:\n" + "\n".join(
            missing_vars
        )
        error_msg += "\n\nPlease set these variables in your environment or .env file."
        raise ConfigurationError(error_msg)


def get_config_summary() -> dict:
    """Get a summary of current configuration (without sensitive data)."""
    config = get_config()
    return {
        "organization": config.organization,
        "base_url": config.base_url,
        "api_token_set": bool(config.api_token),
        "api_token_length": len(config.api_token) if config.api_token else 0,
        "enable_caching": config.enable_caching,
        "debug_mode": config.debug_mode,
    }
