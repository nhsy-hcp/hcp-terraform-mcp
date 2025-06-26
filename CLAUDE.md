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
# Run MCP server (stdio mode)
uv run python -m hcp_terraform_mcp

# Run MCP server in debug mode with Streamable HTTP transport (http://localhost:3000)
TFC_DEBUG_MODE=true uv run python -m hcp_terraform_mcp

# Or use the installed script
uv run hcp-terraform-mcp
```

### Debug Mode with MCP Inspector
```bash
# Start server in debug mode
TFC_DEBUG_MODE=true uv run python -m hcp_terraform_mcp

# In another terminal, run MCP Inspector with Streamable HTTP transport
npx @modelcontextprotocol/inspector http://localhost:3000/mcp
```

## Architecture

### Project Structure
- `src/hcp_terraform_mcp/` - Main package (1,398 total lines)
  - `server.py` - MCP server implementation with tool/resource handlers (165 lines)
  - `client.py` - HCP Terraform API client with rate limiting (392 lines)
  - `config.py` - Configuration management via environment variables (48 lines)
  - `models.py` - Pydantic models for API responses (161 lines)
  - `tool_definitions.py` - Tool schema definitions (313 lines)
  - `tool_handlers.py` - Tool implementation handlers (200 lines)
  - `resource_handlers.py` - Dynamic resource discovery (110 lines)
- `tests/` - Comprehensive test suite with mocked API responses (19 total tests)

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
   - Optional: TFC_BASE_URL, TFC_ENABLE_CACHING, TFC_DEBUG_MODE

## Current Implementation Status

**Phase 1 Complete** ✅
- Project foundation with uv package manager
- HCP Terraform API client with authentication
- Rate limiting and error handling
- Basic MCP server structure
- Test suite with mocking
- Environment-based configuration

**Phase 2 Complete** ✅
- Project management (CRUD operations)
- Workspace management (create, update, lock/unlock)
- Run management (create, apply, cancel runs)
- Full API client implementation
- Comprehensive error handling and validation

**Phase 3 Complete** ✅
- Enhanced resource handlers with dynamic discovery
- 5-minute TTL caching for performance
- 4 comprehensive prompt templates
- Environment validation with clear error messages
- Pydantic models for API response validation
- MCP format compatibility fixes
- MCP Inspector compatibility
- Comprehensive testing (19 tests passing)

**Current MCP Capabilities:**
- Tools: 14 total (1 health + 3 project + 5 workspace + 5 run tools)
- Resources: Dynamic discovery of projects, workspaces, runs + organization info
- Prompts: 4 comprehensive templates (terraform_status, terraform_deployment, workspace_setup, run_monitoring)
- Transport: Dual mode support (stdio for production, Streamable HTTP for debug/development)
- Debug Mode: Full Streamable HTTP server with MCP Inspector compatibility
- Testing: 36 tests covering all functionality including Streamable HTTP transport
- Code Quality: Full type hints, comprehensive error handling, structured logging

## Next Development Phase

Phase 4 will implement API Explorer Integration:
- Advanced analytics and query capabilities
- Organization-wide data exploration
- Infrastructure audit and compliance tools

See `project-plan.md` for complete roadmap.