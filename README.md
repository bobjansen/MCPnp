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
server.run(mode="http", port=8000)
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

### MCP Server Example

The `example_server.py` file demonstrates a clean way to buildMCP tools:

- **Zero Boilerplate**: No `__init__` method or manual registration needed
- **Automatic Schema Generation**: Type hints create JSON schemas automatically
- **Built-in Data Storage**: `MCPDataServer` includes key-value storage methods
- **Metaclass Magic**: Tools auto-register via metaclass when class is defined

#### Available Tools

The example includes these tools:

- `greet` - Greet someone with a personalized message
- `add` - Add two numbers together
- `multiply` - Multiply two numbers
- `store` - Store key-value pairs in memory
- `retrieve` - Retrieve values by key
- `list_keys` - List all stored keys
- `delete` - Delete stored values

#### Running the Example

```bash
# Run the complete example server
uv run python example_server.py
```

#### Tool Definition Syntax

```python
from mcpnp import UnifiedMCPServer, MCPDataServer, tool

class MyMCPServer(MCPDataServer):
    # No __init__ needed! Just define methods with @tool decorators

    @tool("greet", "Greet someone")
    def greet(self, name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}! Welcome to MCPnp!"

    @tool("add", "Add numbers")
    def add_numbers(self, a: float, b: float) -> float:
        return a + b

    @tool("store", "Store data")
    def store_value(self, key: str, value: str) -> str:
        self.store_data(key, value)  # Use built-in storage
        return f"Stored '{key}' successfully"

# Run the server
server = MyMCPServer()
unified_server = UnifiedMCPServer(tool_router=server)
unified_server.run()
```

#### Testing the Tools

**HTTP Mode (easiest for testing):**
```bash
# List available tools
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' \
  http://localhost:8000/

# Call the greet tool
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "greet", "arguments": {"name": "World"}}, "id": 2}' \
  http://localhost:8000/

# Use the add tool
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add", "arguments": {"a": 15, "b": 25}}, "id": 3}' \
  http://localhost:8000/

# Store and retrieve data
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "store", "arguments": {"key": "test", "value": "example"}}, "id": 4}' \
  http://localhost:8000/

curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "retrieve", "arguments": {"key": "test"}}, "id": 5}' \
  http://localhost:8000/
```

**FastMCP Mode (for Claude Desktop integration):**
```bash
# For Claude Desktop, use FastMCP mode
MCP_TRANSPORT=fastmcp uv run python example_server.py
```

### Advanced Router Example

For more complex scenarios, see `mcp_router_example.py` which demonstrates manual tool registration and routing.

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
- **Ruff analysis** - Code quality and standards
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
# Run ruff on all code
uv run ruff check mcpnp/ tests/ *.py
```

## Documentation

See the main documentation for detailed setup instructions and examples.

## License

AGPL-3.0-or-later
