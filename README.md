# HCP Terraform MCP Server

A Model Context Protocol (MCP) server that provides AI agents with standardized access to HCP Terraform APIs for managing projects, workspaces, and runs.

## Project Status - Phase 3 Complete ✅

All three implementation phases have been completed, providing a full-featured MCP server for HCP Terraform management.

### Completed Features

**Phase 1 - Foundation:**
- Python project initialization with uv package manager
- MCP Python SDK and HTTP client dependencies
- Development environment and testing framework setup
- HCP Terraform API client with authentication
- Rate limiting (30 requests/second compliance)
- JSON API response parsing and error handling
- Basic MCP server structure with health check tool
- Configuration management via environment variables
- Basic test suite

**Phase 2 - Core Operations:**
- Project management (CRUD operations)
- Workspace management (create, update, lock/unlock)
- Run management (create, apply, cancel runs)
- Full API client implementation
- Comprehensive error handling and validation

**Phase 3 - Advanced Features:**
- Enhanced resource handlers with dynamic discovery
- 5-minute TTL caching for performance optimization
- 4 comprehensive prompt templates
- Environment validation with clear error messages
- Pydantic models for API response validation
- MCP format compatibility fixes
- MCP Inspector compatibility
- Comprehensive testing suite (19 tests passing)

### Project Structure

```
hcp-terraform-mcp/
  src/hcp_terraform_mcp/
    __init__.py
    __main__.py               # Main entry point
    server.py                 # MCP server implementation (165 lines)
    client.py                 # HCP Terraform API client (392 lines)
    config.py                 # Configuration management (48 lines)
    models.py                 # Pydantic models for API responses (161 lines)
    tool_definitions.py       # Tool definitions (313 lines)
    tool_handlers.py          # Tool implementation handlers (200 lines)
    resource_handlers.py      # Resource discovery handlers (110 lines)
  tests/
    test_client.py            # Client tests (14 tests)
    test_server.py            # Server tests (5 tests)
  .env.example              # Environment variables template
  pytest.ini                # Test configuration
  project-plan.md           # Implementation plan
  pyproject.toml            # Project dependencies
  CLAUDE.md                 # Claude Code guidance
```

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your HCP Terraform credentials
   ```

3. **Run tests:**
   ```bash
   uv run pytest
   ```

4. **Run the MCP server:**
   ```bash
   uv run python -m hcp_terraform_mcp
   ```

5. **Run with MCP Inspector (for debugging/testing):**
   ```bash
   # Install MCP Inspector
   npx @modelcontextprotocol/inspector uv run python -m hcp_terraform_mcp
   ```
   
   This will start the MCP Inspector web interface, allowing you to:
   - Inspect available tools, resources, and prompts
   - Test tool calls interactively
   - Debug MCP server responses
   - View server logs and performance metrics

## Configuration

Set these environment variables in your `.env` file:

- `TFC_API_TOKEN`: Your HCP Terraform API token (required)
- `TFC_ORGANIZATION`: Your organization name (required)
- `TFC_BASE_URL`: API base URL (default: https://app.terraform.io/api/v2)
- `TFC_ENABLE_CACHING`: Enable 5-minute response caching (default: true)
- `TFC_DEBUG_MODE`: Enable debug logging (default: false)

## Current MCP Capabilities

### Tools (14 total)
**Health & Connectivity:**
- `health_check` - Check HCP Terraform API connectivity

**Project Management:**
- `create_project` - Create a new HCP Terraform project
- `list_projects` - List all projects in the organization
- `delete_project` - Delete a project by ID

**Workspace Management:**
- `create_workspace` - Create a new workspace
- `list_workspaces` - List workspaces (with optional project filtering)
- `update_workspace` - Update workspace settings
- `lock_workspace` - Lock a workspace to prevent changes
- `unlock_workspace` - Unlock a workspace

**Run Management:**
- `create_run` - Create and execute a new run
- `list_runs` - List runs for a workspace
- `get_run` - Get detailed information about a specific run
- `apply_run` - Apply a planned run
- `cancel_run` - Cancel a running operation

### Resources
- `terraform://organization/info` - Organization details and metadata
- `terraform://projects/` - Dynamic discovery of all projects
- `terraform://workspaces/` - Dynamic discovery of all workspaces
- `terraform://runs/` - Dynamic discovery of recent runs

### Prompts (4 comprehensive templates)
- `terraform_status` - Organization and infrastructure status overview
- `terraform_deployment` - Deployment planning and execution guidance
- `workspace_setup` - Workspace configuration and management
- `run_monitoring` - Run execution monitoring and troubleshooting

## Adding to Claude Code

Once you have the MCP server set up locally, you can add it to Claude Code:

### Prerequisites

1. **Install the MCP server:**
   ```bash
   # From the project directory
   uv sync
   uv pip install -e .
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your HCP Terraform credentials:
   # TFC_API_TOKEN=your_terraform_cloud_api_token_here
   # TFC_ORGANIZATION=your_organization_name
   # TFC_BASE_URL=https://app.terraform.io/api/v2
   ```

### Adding the Server to Claude Code

#### Option 1: Project-Specific Configuration
Add the server to your current project:

```bash
claude mcp add hcp-terraform \
  -e TFC_API_TOKEN=your_token_here \
  -e TFC_ORGANIZATION=your_org_name \
  -e TFC_BASE_URL=https://app.terraform.io/api/v2 \
  -- uv run hcp-terraform-mcp
```

#### Option 2: User-Wide Configuration
Add the server for all Claude Code sessions:

```bash
claude mcp add hcp-terraform \
  --scope user \
  -e TFC_API_TOKEN=your_token_here \
  -e TFC_ORGANIZATION=your_org_name \
  -e TFC_BASE_URL=https://app.terraform.io/api/v2 \
  -- uv run hcp-terraform-mcp
```

#### Option 3: Using Environment File
If you prefer to use the `.env` file:

```bash
# First, ensure your .env file is properly configured
claude mcp add hcp-terraform \
  -- bash -c "source .env && uv run hcp-terraform-mcp"
```

### Verify Installation

Check that the server is configured correctly:

```bash
# List all MCP servers
claude mcp list

# Get details about the HCP Terraform server
claude mcp get hcp-terraform
```

### Usage in Claude Code

Once added, you can use the server's comprehensive capabilities in Claude Code:

**Project Management:**
- Create, list, and delete projects
- Organize workspaces within projects

**Workspace Operations:**
- Create and configure workspaces
- Update workspace settings and variables
- Lock/unlock workspaces for maintenance

**Infrastructure Deployment:**
- Create and execute runs
- Monitor run progress and logs
- Apply planned changes
- Cancel running operations

**Resource Discovery:**
- Browse all projects, workspaces, and runs
- Get detailed information about infrastructure state

**Guided Workflows:**
- Use prompt templates for common scenarios
- Get assistance with deployment planning
- Monitor infrastructure health

### Troubleshooting

**Server not starting:**
- Verify your API token has the correct permissions
- Check that the organization name is spelled correctly
- Ensure the server is installed: `uv pip install -e .`

**Permission errors:**
- Your API token needs read access to the organization
- For write operations (in future phases), you'll need appropriate workspace permissions

**Connection issues:**
- Verify `TFC_BASE_URL` is correct for your HCP Terraform instance
- Check network connectivity to HCP Terraform

### Removing the Server

If you need to remove the server:

```bash
claude mcp remove hcp-terraform
```

## Next Development Phase

Phase 4 (Future) - API Explorer Integration:
- Advanced analytics and query capabilities
- Organization-wide data exploration
- Infrastructure audit and compliance tools
- Custom reporting and metrics

See `implementation-plan.md` for the complete development roadmap.

## Technical Specifications

- **Language**: Python 3.11+
- **Framework**: MCP (Model Context Protocol) Python SDK
- **API Client**: HTTP client with rate limiting (30 req/sec)
- **Caching**: 5-minute TTL for performance optimization
- **Testing**: 19 comprehensive tests with mocked API responses
- **Code Quality**: Type hints, error handling, and logging throughout