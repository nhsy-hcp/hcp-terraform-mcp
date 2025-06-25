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

### Phase 1: Foundation ✅ COMPLETE
1. **Project Setup** ✅
   - Initialize Python project with uv package manager
   - Install MCP Python SDK and HTTP client dependencies
   - Set up development environment and testing framework

2. **Authentication & Base Client** ✅
   - Implement HCP Terraform API client
   - Add authentication handling
   - Create base request/response handling

### Phase 2: Core Tools ✅ COMPLETE
1. **Project Tools** ✅
   - Implement project create, read, and update operations
   - Add project listing and filtering

2. **Workspace Tools** ✅
   - Implement workspace management operations
   - Add workspace state management (lock/unlock)

3. **Run Tools** ✅
   - Implement run lifecycle management
   - Add run creation and monitoring

### ✅ Phase 3: Resources & Prompts - COMPLETED
1. **Resource Implementation** ✅
   - Added read-only data access for projects, workspaces, runs
   - Implemented 5-minute TTL caching for frequently accessed data
   - Enhanced resource URIs: `terraform://project/{id}`, `terraform://workspace/{id}`, `terraform://run/{id}`

2. **Prompt Templates** ✅
   - Created 4 helpful prompt templates for common operations
   - `terraform_deployment` - Plan and execute deployments
   - `workspace_setup` - Set up new workspaces  
   - `run_monitoring` - Monitor run status
   - Enhanced existing `terraform_status` template

3. **Environment Variable Validation** ✅
   - Added environment validation for required variables (TFC_API_TOKEN, TFC_ORGANIZATION)
   - Enhanced configuration error handling with clear error messages
   - Added ConfigurationError exception class

4. **Pydantic Validation** ✅
   - Added validation for API responses with Pydantic models
   - Created ProjectAttributes, WorkspaceAttributes, RunAttributes models
   - Graceful fallback when validation fails

5. **Testing** ✅
   - Updated test suite with 14 comprehensive tests (all passing)
   - Added tests for caching, validation, and error handling
   - Enhanced test coverage for Phase 3 functionality

6. **MCP Format Compatibility** ✅
   - Fixed MCP format issues for compatibility with MCP Inspector
   - Updated return formats for all handlers (list_tools, call_tool, etc.)
   - Ensured compatibility with MCP Python SDK requirements

### Phase 4: API Explorer Integration
1. **Explorer Tools**
   - `query_workspaces` - Query workspace data across organization
   - `query_terraform_versions` - Analyze Terraform version usage
   - `query_providers` - Explore provider usage across workspaces
   - `query_modules` - Analyze module usage patterns

2. **Explorer Resources**
   - `explorer://organization/workspaces` - Organization-wide workspace data
   - `explorer://organization/providers` - Provider usage analytics
   - `explorer://organization/modules` - Module usage analytics
   - `explorer://organization/versions` - Terraform version distribution

3. **Explorer Prompts**
   - `infrastructure_audit` - Template for comprehensive infrastructure analysis
   - `version_compliance` - Template for version standardization analysis
   - `provider_inventory` - Template for provider usage reporting

### Phase 5: Testing & Documentation
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

## Estimated Timeline:
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
- `src/hcp_terraform_mcp/server.py` - MCP server implementation
- `src/hcp_terraform_mcp/client.py` - HCP Terraform API client
- `src/hcp_terraform_mcp/config.py` - Configuration management
- `src/hcp_terraform_mcp/models.py` - Pydantic models for API responses
- `tests/test_client.py` - Client test suite
- `tests/test_server.py` - Server test suite
- `.env.example` - Environment configuration template

**Current MCP Capabilities:**
- Tool: `health_check` - API connectivity testing
- Resource: `terraform://organization/info` - Organization information
- Prompt: `terraform_status` - Status check template

### ✅ Phase 2: Core Tools - COMPLETED
**Completed Features:**
- **Project Management Tools:** `create_project`, `update_project`, `list_projects`
- **Workspace Management Tools:** `create_workspace`, `update_workspace`, `list_workspaces`, `lock_workspace`, `unlock_workspace`
- **Run Management Tools:** `create_run`, `apply_run`, `cancel_run`, `discard_run`, `list_runs`
- Full API client implementation with all CRUD operations
- Comprehensive error handling and validation
- Test coverage for all new functionality (20/22 tests passing)

**Current MCP Capabilities:**
- Tools: 12 total (1 health + 3 project + 5 workspace + 5 run tools)
- Resources: `terraform://organization/info` - Organization information
- Prompts: `terraform_status` - Status check template

### ✅ Phase 3: Resources & Prompts - COMPLETED
**Completed Features:**
- **Enhanced Resource Handlers:** Dynamic resource discovery with caching
- **5-minute TTL Caching:** Improves performance for frequently accessed data
- **4 Prompt Templates:** Comprehensive templates for common Terraform operations
- **Environment Validation:** Robust validation with clear error messages
- **Pydantic Models:** Data validation for API responses with graceful fallback
- **MCP Format Compatibility:** All handlers now compatible with MCP Inspector
- **Comprehensive Testing:** 14 tests covering all new functionality

**Current MCP Capabilities:**
- Tools: 12 total (1 health + 3 project + 5 workspace + 5 run tools)
- Resources: Dynamic discovery of projects, workspaces, runs + organization info
- Prompts: 4 comprehensive templates (terraform_status, terraform_deployment, workspace_setup, run_monitoring)

### 🔄 Next: Phase 4 - API Explorer Integration
Ready to implement advanced analytics and query capabilities.

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

#### Explorer API
- `GET /api/explorer/v1/organizations/:organization_name/workspaces` - Query workspaces
- `GET /api/explorer/v1/organizations/:organization_name/terraform-versions` - Query Terraform versions
- `GET /api/explorer/v1/organizations/:organization_name/providers` - Query providers
- `GET /api/explorer/v1/organizations/:organization_name/modules` - Query modules