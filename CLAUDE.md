# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HCP Terraform MCP Server - A Model Context Protocol server that provides AI agents with standardized access to HCP Terraform APIs for managing projects, workspaces, and runs.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your HCP Terraform credentials
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests excluding slow rate limiter tests
uv run pytest -k "not rate_limiter"

# Run with coverage
uv run pytest --cov=src/hcp_terraform_mcp
```

### Running the Server
```bash
# Run MCP server
uv run python -m hcp_terraform_mcp

# Or use the installed script
uv run hcp-terraform-mcp
```

## Architecture

### Project Structure
- `src/hcp_terraform_mcp/` - Main package
  - `server.py` - MCP server implementation with tool/resource handlers
  - `client.py` - HCP Terraform API client with rate limiting
  - `config.py` - Configuration management via environment variables
  - `models.py` - Pydantic models for API responses
- `tests/` - Test suite with mocked API responses

### Key Components

1. **TerraformClient** - HTTP client wrapper for HCP Terraform API
   - Handles authentication via bearer tokens
   - Implements rate limiting (30 req/sec)
   - Parses JSON API responses with error handling

2. **TerraformMcpServer** - MCP server implementation
   - Exposes tools, resources, and prompts for AI agents
   - Manages client lifecycle and error handling

3. **Configuration** - Environment-based config management
   - Required: TFC_API_TOKEN, TFC_ORGANIZATION
   - Optional: TFC_BASE_URL

## Current Implementation Status

**Phase 1 Complete** ✅
- Project foundation with uv package manager
- HCP Terraform API client with authentication
- Rate limiting and error handling
- Basic MCP server structure
- Test suite with mocking
- Environment-based configuration

**Current MCP Capabilities:**
- Tools: `health_check` - API connectivity test
- Resources: `terraform://organization/info` - Organization details
- Prompts: `terraform_status` - Status check template

## Next Development Phase

Phase 2 will implement core Terraform operations:
- Project management (CRUD operations)
- Workspace management (create, update, lock/unlock)
- Run management (create, apply, cancel runs)
- Enhanced resources and prompts

See `project-plan.md` for complete roadmap.