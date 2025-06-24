# HCP Terraform MCP Server - Project Plan

## Project Overview
Build a Python MCP (Model Context Protocol) server that provides AI agents with standardized access to HCP Terraform APIs for managing projects, workspaces, and runs.

## Architecture Design

### Core Components
1. **MCP Server Foundation**
   - FastMCP-based Python server using the official MCP Python SDK
   - Async/await pattern for API calls
   - Proper lifecycle management with startup/shutdown hooks

2. **Authentication Layer**
   - Support for multiple HCP Terraform token types (User, Team, Organization)
   - Secure token management via environment variables
   - Rate limiting compliance (30 requests/second)

3. **API Client Layer**
   - HTTP client wrapper for HCP Terraform API
   - JSON API specification support
   - Error handling and retry logic

## MCP Capabilities

### Tools (AI-Callable Functions)
**Project Management:**
- `create_project` - Create new Terraform project
- `update_project` - Update project settings
- `list_projects` - List organization projects

**Workspace Management:**
- `create_workspace` - Create new workspace
- `update_workspace` - Update workspace configuration
- `lock_workspace` / `unlock_workspace` - Workspace locking
- `list_workspaces` - List workspaces with filtering

**Run Management:**
- `create_run` - Trigger Terraform runs
- `apply_run` - Apply pending runs
- `cancel_run` / `discard_run` - Run lifecycle management
- `list_runs` - List runs with filtering

### Resources (Data Access)
- `project_details` - Read project information
- `workspace_details` - Read workspace configuration
- `run_details` - Read run status and logs
- `organization_info` - Organization metadata

### Prompts (Templates)
- `terraform_deployment` - Template for deploying infrastructure
- `workspace_setup` - Template for workspace configuration
- `run_monitoring` - Template for monitoring run status

## Implementation Plan

### Phase 1: Foundation (2-3 days) ✅ COMPLETE
1. **Project Setup** ✅
   - Initialize Python project with uv package manager
   - Install MCP Python SDK and HTTP client dependencies
   - Set up development environment and testing framework

2. **Authentication & Base Client** ✅
   - Implement HCP Terraform API client
   - Add authentication handling
   - Create base request/response handling

### Phase 2: Core Tools (3-4 days)
1. **Project Tools**
   - Implement project CRUD operations
   - Add project listing and filtering

2. **Workspace Tools**
   - Implement workspace management operations
   - Add workspace state management (lock/unlock)

3. **Run Tools**
   - Implement run lifecycle management
   - Add run creation and monitoring

### Phase 3: Resources & Prompts (2 days)
1. **Resource Implementation**
   - Add read-only data access for projects, workspaces, runs
   - Implement proper caching for frequently accessed data

2. **Prompt Templates**
   - Create helpful prompt templates for common operations
   - Add documentation and examples

### Phase 4: Testing & Documentation (2 days)
1. **Testing**
   - Unit tests for all tools and resources
   - Integration tests with mock HCP Terraform API
   - Error handling validation

2. **Documentation**
   - README with setup and usage instructions
   - API documentation for all tools/resources
   - Configuration examples

## Technical Specifications

### Dependencies
- `mcp` - Official MCP Python SDK
- `httpx` - Async HTTP client
- `pydantic` - Data validation
- `pytest` - Testing framework

### Configuration
```python
# Environment variables
TFC_API_TOKEN=<your-token>
TFC_ORGANIZATION=<org-name>
TFC_BASE_URL=https://app.terraform.io/api/v2
```

### Error Handling
- API rate limiting respect
- Comprehensive error messages
- Graceful fallbacks for missing permissions
- Validation of required parameters

### Security Considerations
- No token storage in code
- Secure credential handling
- Permission validation before operations
- Audit logging for destructive operations

## Success Criteria
1. All major HCP Terraform operations accessible via MCP
2. Comprehensive test coverage (>90%)
3. Clear documentation and examples
4. Production-ready error handling
5. Compatible with Claude Desktop and other MCP clients

## Estimated Timeline: 10-12 days
This plan provides a production-ready MCP server that enables AI agents to effectively manage HCP Terraform infrastructure through standardized protocols.

## Implementation Status

### ✅ Phase 1: Foundation - COMPLETED
**Completed Features:**
- Python project setup with uv package manager
- MCP Python SDK and HTTP client dependencies installed
- Development environment with pytest testing framework
- HCP Terraform API client with bearer token authentication
- Rate limiting implementation (30 requests/second)
- JSON API response parsing with comprehensive error handling
- Basic MCP server structure with health check tool
- Configuration management via environment variables
- Test suite with 8 passing tests (6 core + 2 rate limiter)
- Documentation updates (CLAUDE.md, README.md)

**Files Created:**
- `src/tfc_mcp/server.py` - MCP server implementation
- `src/tfc_mcp/client.py` - HCP Terraform API client
- `src/tfc_mcp/config.py` - Configuration management
- `src/tfc_mcp/models.py` - Pydantic models for API responses
- `tests/test_client.py` - Client test suite
- `tests/test_server.py` - Server test suite
- `.env.example` - Environment configuration template

**Current MCP Capabilities:**
- Tool: `health_check` - API connectivity testing
- Resource: `terraform://organization/info` - Organization information
- Prompt: `terraform_status` - Status check template

### 🔄 Next: Phase 2 - Core Tools
Ready to implement project, workspace, and run management operations.

## HCP Terraform API Reference

### Authentication
- Uses bearer token authentication in Authorization header
- Supports User, Team, Organization, and Audit Trail tokens
- Rate limit: 30 requests per second for most endpoints

### Key API Endpoints

#### Projects API
- `POST /organizations/:organization_name/projects` - Create project
- `PATCH /projects/:project_id` - Update project
- `GET /organizations/:organization_name/projects` - List projects
- `GET /projects/:project_id` - Show project details

#### Workspaces API
- `POST /organizations/:organization_name/workspaces` - Create workspace
- `PATCH /workspaces/:workspace_id` - Update workspace
- `GET /organizations/:organization_name/workspaces` - List workspaces
- `GET /workspaces/:workspace_id` - Show workspace details
- `POST /workspaces/:workspace_id/actions/lock` - Lock workspace
- `POST /workspaces/:workspace_id/actions/unlock` - Unlock workspace

#### Runs API
- `POST /runs` - Create run
- `POST /runs/:run_id/actions/apply` - Apply run
- `GET /workspaces/:workspace_id/runs` - List workspace runs
- `GET /organizations/:organization_name/runs` - List organization runs
- `GET /runs/:run_id` - Get run details
- `POST /runs/:run_id/actions/discard` - Discard run
- `POST /runs/:run_id/actions/cancel` - Cancel run
- `POST /runs/:run_id/actions/force-cancel` - Force cancel run