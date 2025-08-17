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
