# MCPnp - Model Context Protocol and Play

A generic, reusable framework for building MCP (Model Context Protocol) servers with multiple transport modes, authentication systems, and user management capabilities.

## Features

- **Multiple Transport Modes**: FastMCP (local), HTTP REST API, OAuth 2.1, Server-Sent Events
- **Authentication Systems**: Token-based auth, OAuth 2.1 with multi-user support
- **User Management**: Built-in user session handling and database isolation
- **Extensible Architecture**: Easy to integrate with any backend data source
- **Production Ready**: Includes error handling, logging, and monitoring

## Quick Start

```python
from mcpnp import UnifiedMCPServer, MCPContext

# Create an MCP server instance
server = UnifiedMCPServer()

# Define your tools
@server.tool("my_tool")
def my_tool(param: str) -> str:
    return f"Hello {param}"

# Start the server
server.run()
```

## Transport Modes

### Local Mode (FastMCP)
Perfect for Claude Desktop integration:
```python
server.run(mode="local")
```

### HTTP REST API
For web applications and API integration:
```python
server.run(mode="http", port=8080)
```

### OAuth Multi-User
For applications requiring user authentication:
```python
server.run(mode="oauth", multiuser=True)
```

## Installation

```bash
pip install mcpnp
```

## Examples

### MCP Router Example

The `mcp_router_example.py` file provides a self-contained example of building MCP tools with the framework. It demonstrates:

- **Tool Definition**: How to define tools with proper JSON schemas
- **Tool Routing**: Dispatching tool calls to appropriate implementations
- **Data Storage**: Simple in-memory key-value storage
- **Error Handling**: Proper error responses and exception handling

#### Available Tools

The example includes these tools:

- `echo` - Echo back any message
- `add_data` - Store key-value pairs in memory
- `get_data` - Retrieve values by key
- `list_data` - List all stored keys
- `calculate` - Basic arithmetic operations (add, subtract, multiply, divide)

#### Running the Example

```bash
# Run the standalone example (just prints test output)
uv run python mcp_router_example.py
```

#### Interactive Usage

To actually interact with the MCP tools, you need to run the server with the tool router:

**HTTP Mode (easiest for testing):**
```bash
# Create a simple script to run the server with the example router
cat > test_server.py << 'EOF'
from mcp_router_example import MCPToolRouter
from mcpnp import UnifiedMCPServer
import os

os.environ['MCP_TRANSPORT'] = 'http'
os.environ['MCP_HOST'] = 'localhost'
os.environ['MCP_PORT'] = '8080'

router = MCPToolRouter()
server = UnifiedMCPServer(tool_router=router)
server.run()
EOF

# Run the server
uv run python test_server.py
```

**Test the tools with curl:**
```bash
# List available tools
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' \
  http://localhost:8080/

# Call the echo tool
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "echo", "arguments": {"message": "Hello World!"}}, "id": 2}' \
  http://localhost:8080/

# Store some data
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add_data", "arguments": {"key": "test", "value": "example"}}, "id": 3}' \
  http://localhost:8080/

# Retrieve the data
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_data", "arguments": {"key": "test"}}, "id": 4}' \
  http://localhost:8080/
```

**FastMCP Mode (for Claude Desktop integration):**
```bash
# For Claude Desktop, use FastMCP mode
MCP_TRANSPORT=fastmcp uv run python -c "
from mcp_router_example import MCPToolRouter
from mcpnp import UnifiedMCPServer
router = MCPToolRouter()
server = UnifiedMCPServer(tool_router=router)
server.run()
"
```

#### Example Usage

```python
from mcp_router_example import MCPToolRouter

# Create router instance
router = MCPToolRouter()

# Use the tools
echo_result = router.call_tool("echo", {"message": "Hello!"})
router.call_tool("add_data", {"key": "name", "value": "MCPnp"})
data_result = router.call_tool("get_data", {"key": "name"})
calc_result = router.call_tool("calculate", {"operation": "add", "a": 5, "b": 3})

# Get available tools
tools = router.get_available_tools()
```

## Development

### Code Quality Checks

This project includes a comprehensive code quality check script:

```bash
# Run all checks (formatting, linting, tests)
python check.py

# Quick mode (faster, skip some checks)
python check.py --quick

# Auto-fix formatting issues
python check.py --fix
```

The script validates:
- **Black formatting** - Code style consistency
- **Pylint analysis** - Code quality and standards
- **Pytest execution** - All tests pass

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_mcp_e2e.py -v

# Quick test run
uv run pytest tests/ --tb=line -q
```

### Code Formatting

```bash
# Check formatting
uv run black --check --diff .

# Auto-fix formatting
uv run black .
```

### Linting

```bash
# Run pylint on all code
uv run pylint mcpnp/ tests/ *.py
```

## Documentation

See the main documentation for detailed setup instructions and examples.

## License

AGPL-3.0-or-later
