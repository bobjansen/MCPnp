# MCPnp Installation Guide

MCPnp is a modern Python package that can be installed using pip or uv.

## Requirements

- Python 3.12 or higher
- pip or uv package manager

## Installation Methods

### 1. Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/mcpnp.git
cd mcpnp

# Install in development mode with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### 2. Install from PyPI (when published)

```bash
# With uv (recommended)
uv pip install mcpnp

# Or with pip
pip install mcpnp
```

### 3. Install with Optional Dependencies

```bash
# Install with development tools
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Verify Installation

After installation, you should have access to the following commands:

```bash
# Show version information
mcpnp version

# Start a server
mcpnp server fastmcp

# Run quality checks
mcpnp check

# Direct server launcher
mcpnp-server --help
```

## Quick Start

1. **Start a local FastMCP server:**
   ```bash
   mcpnp server fastmcp --local
   ```

2. **Start an HTTP server:**
   ```bash
   mcpnp server http --port 8000
   ```

3. **Start an OAuth multi-user server:**
   ```bash
   mcpnp server oauth --multiuser --port 9000
   ```

## Development Installation

For development work:

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/mcpnp.git
cd mcpnp
uv pip install -e ".[dev]"

# Run tests
mcpnp check

# Or run individual tools
uv run pytest
uv run black --check .
uv run pylint mcpnp/
```

## Environment Variables

MCPnp can be configured with environment variables:

- `MCP_TRANSPORT`: Transport mode (fastmcp, http, oauth, sse)
- `MCP_MODE`: Authentication mode (local, multiuser)
- `MCP_HOST`: Server host (default: localhost)
- `MCP_PORT`: Server port (default: 8000)
- `MCP_PUBLIC_URL`: Public URL for OAuth mode
- `MCP_LOG_DIR`: Log directory (default: logs)

## Troubleshooting

### Common Issues

1. **Python version mismatch:**
   ```bash
   python --version  # Should be 3.12+
   ```

2. **Missing dependencies:**
   ```bash
   uv pip install --upgrade mcpnp
   ```

3. **Permission issues:**
   ```bash
   # Use virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install mcpnp
   ```

### Getting Help

- Check the [documentation](README.md)
- View example usage: `mcpnp --help`
- Report issues on [GitHub](https://github.com/yourusername/mcpnp/issues)
