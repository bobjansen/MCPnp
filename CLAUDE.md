# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this MCPnp repository.

## Project Overview

MCPnp is a comprehensive **Model Context Protocol (MCP) server framework** that provides:
- Multiple transport modes (FastMCP, HTTP REST, SSE, OAuth 2.1)
- Authentication and user management
- Flexible tool routing system
- Production-ready security features

## Common Development Commands

### Code Quality Checks
**Use the integrated check script for all quality validation:**
```bash
# Run all checks (formatting, linting, tests)
python check.py

# Quick mode (faster, skip some checks)
python check.py --quick

# Auto-fix formatting issues
python check.py --fix
```

### Running the Application
All scripts and applications run through uv using `uv run`:
```bash
# Start MCP server
uv run python run_mcp.py

# Run with specific transport
MCP_TRANSPORT=http uv run python run_mcp.py
```

### Testing
```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_mcp_e2e.py -v

# Quick test run
uv run pytest tests/ --tb=line -q
```

### Code Formatting & Linting
```bash
# Check formatting
uv run black --check --diff .

# Auto-fix formatting
uv run black .

# Run pylint
uv run pylint mcpnp/ tests/ *.py
```

### Environment Setup
```bash
# Install dependencies
uv sync

# Add new dependency
uv add package_name
```

## Architecture Overview

### Core Components

**UnifiedMCPServer (`mcpnp/server/unified_server.py`)**
- Multi-transport MCP server supporting FastMCP, HTTP, SSE, and OAuth 2.1
- Environment-driven configuration through MCP_TRANSPORT and MCP_MODE
- Integrated authentication and user management
- Production-ready with logging, CORS, and security features

**Tool Router (`mcp_tool_router.py`)**
- Provides mock/stub MCP tools for testing and development
- Implements authentication-dependent tools
- Handles tool registration and execution
- Includes error handling and logging

**Authentication System (`mcpnp/auth/`)**
- OAuth 2.1 server with PKCE support (`oauth_server.py`)
- User management with encrypted password storage (`user_manager.py`)
- Database abstractions for SQLite and PostgreSQL (`datastore_*.py`)
- OAuth handlers for authorization flows (`oauth_handlers.py`)

**Transport Modes**
- **FastMCP**: stdio-based transport for direct CLI integration
- **HTTP**: RESTful API with FastAPI backend
- **SSE**: Server-Sent Events for real-time updates
- **OAuth**: Full OAuth 2.1 authentication with web interface

### Configuration

**Environment Variables:**
- `MCP_TRANSPORT`: `fastmcp|http|sse|oauth` (default: `fastmcp`)
- `MCP_MODE`: `local|remote|multiuser` (default: `local`)
- `MCP_HOST`: Server host (default: `localhost`)
- `MCP_PORT`: Server port (default: `8000`)
- `MCP_PUBLIC_URL`: Public URL for OAuth redirects
- `ADMIN_TOKEN`: Admin authentication token
- `USER_DATA_DIR`: Directory for user data storage

## Development Guidelines

### Adding New MCP Tools

1. **Add tool definition** in `mcp_tool_router.py`:
```python
def get_available_tools(self):
    return [
        {
            "name": "my_new_tool",
            "description": "Description of what the tool does",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Parameter description"}
                }
            }
        }
    ]
```

2. **Implement tool method**:
```python
def _my_new_tool(self, arguments: Dict[str, Any], manager=None) -> Dict[str, Any]:
    """Implementation of the new tool."""
    try:
        # Tool logic here
        return {"status": "success", "result": "..."}
    except Exception as e:
        log_tool_error(e, "my_new_tool")
        return {"status": "error", "message": str(e)}
```

3. **Register in tool dispatch**:
```python
def call_tool(self, name: str, arguments: Dict[str, Any], manager=None):
    tools = {
        # ... existing tools
        "my_new_tool": self._my_new_tool,
    }
```

### Authentication-Dependent Tools

For tools that require authentication:
```python
def _authenticated_tool(self, arguments: Dict[str, Any], manager=None) -> Dict[str, Any]:
    """Tool that requires authentication."""
    if manager is None:
        return {
            "status": "error",
            "message": "Authentication required - no user session"
        }

    user_id = getattr(manager, "user_id", "unknown")
    # Tool implementation with authenticated user context
```

### Testing Guidelines

**Test Categories:**
- `test_mcp_e2e.py`: End-to-end protocol testing
- `test_mcp_server_startup.py`: Server configuration and startup
- `test_mcp_transport_modes.py`: Transport mode validation
- `test_oauth_redirect_uri_matching.py`: OAuth security testing

**Test Patterns:**
- Use `MCPToolRouter()` for tool testing
- Use `UnifiedMCPServer(tool_router=tool_router)` for server testing
- Mock OAuth datastores with `MagicMock()` when needed
- Use `cleanup_test_environment()` in teardown methods

### Security Best Practices

- **OAuth Implementation**: Full OAuth 2.1 with PKCE support
- **Password Security**: Scrypt hashing with werkzeug
- **Token Security**: Cryptographically secure token generation
- **Input Validation**: Comprehensive parameter validation
- **Error Handling**: No sensitive information in error messages

### Code Quality Standards

**Required Checks (all must pass):**
- ✅ **Black formatting**: Consistent code style
- ✅ **Pylint analysis**: Code quality > 9.5/10 (configured for MCP servers)
- ✅ **Pytest execution**: All tests pass (39/39)

**Pylint Configuration:**
- Custom `.pylintrc` designed for MCP server development
- Allows reasonable complexity (max-args=10, max-attributes=15)
- Disables warnings common in protocol implementations
- Focus on real code quality issues, not architectural constraints

**Performance Targets:**
- Test suite: < 3 seconds
- Server startup: < 1 second
- OAuth flows: < 500ms per request

### Deployment Modes

**Local Development:**
```bash
MCP_TRANSPORT=fastmcp MCP_MODE=local uv run python run_mcp.py
```

**HTTP Server:**
```bash
MCP_TRANSPORT=http MCP_MODE=remote MCP_PORT=8000 uv run python run_mcp.py
```

**OAuth Multi-user:**
```bash
MCP_TRANSPORT=oauth MCP_MODE=multiuser MCP_PUBLIC_URL=https://your-domain.com uv run python run_mcp.py
```

## Troubleshooting

### Common Issues

**Tests hanging**: Check `test_sse_events_endpoint_mock` - SSE endpoints use infinite streams
**Import errors**: Ensure `uv sync` has been run and all dependencies installed
**OAuth errors**: Verify `MCP_PUBLIC_URL` matches your actual domain
**Port conflicts**: Change `MCP_PORT` environment variable

### Debug Mode
```bash
# Enable verbose logging
PYTHONPATH=. LOG_LEVEL=DEBUG uv run python run_mcp.py
```

### Quality Checks Failing
```bash
# Fix formatting issues
python check.py --fix

# Review specific pylint issues
uv run pylint mcpnp/ --disable=import-error

# Debug test failures
uv run pytest tests/ -v --tb=long
```

## Important Notes

- **Always run quality checks** before committing: `python check.py`
- **SSE endpoints are infinite streams** - don't consume content in tests
- **OAuth requires datastore** - provide mock datastore in tests
- **Environment isolation** - use `cleanup_test_environment()` in tests
- **Security first** - never commit tokens or sensitive data
