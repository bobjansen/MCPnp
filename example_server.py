"""
MCP Server Example - Comprehensive example with command line interface.

This example demonstrates how to create an MCP server using the decorator-based
approach with full command line configuration support.
"""

import argparse
import os
import sys
from typing import List
from mcpnp import UnifiedMCPServer, MCPDataServer, tool
from mcpnp.auth.datastore_postgresql import PostgreSQLOAuthDatastore
from mcpnp.auth.datastore_sqlite import SQLiteOAuthDatastore


class MyMCPServer(MCPDataServer):
    """MCP server example with decorator-based tool registration."""

    @tool("greet", "Greet someone with a personalized message")
    def greet(self, name: str, greeting: str = "Hello") -> str:
        """Greet someone with a personalized message."""
        return f"{greeting}, {name}! Welcome to MCPnp!"

    @tool("add", "Add two numbers together")
    def add_numbers(self, a: float, b: float) -> float:
        """Add two numbers and return the result."""
        return a + b

    @tool("multiply", "Multiply two numbers")
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers and return the result."""
        return a * b

    @tool("store", "Store a value with a key")
    def store_value(self, key: str, value: str) -> str:
        """Store a key-value pair."""
        self.store_data(key, value)
        return f"Stored '{key}' successfully"

    @tool("retrieve", "Retrieve a stored value by key")
    def retrieve_value(self, key: str) -> str:
        """Retrieve a value by its key."""
        try:
            return self.get_data(key)
        except KeyError as e:
            return f"Error: {str(e)}"

    @tool("list_keys", "List all stored keys")
    def list_stored_keys(self) -> List[str]:
        """List all stored keys."""
        return self.list_keys()

    @tool("delete", "Delete a stored value")
    def delete_value(self, key: str) -> str:
        """Delete a stored value."""
        if self.delete_data(key):
            return f"Deleted '{key}' successfully"
        return f"Key '{key}' not found"


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="MCPnp Example Server - Decorator-based MCP tool server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # HTTP server on localhost:8000
  %(prog)s --transport fastmcp               # FastMCP for Claude Desktop
  %(prog)s --transport http --port 8080      # HTTP server on port 8080
  %(prog)s --transport oauth --multiuser     # OAuth server with multi-user support
  %(prog)s --host 0.0.0.0 --port 3000        # HTTP server accessible from all interfaces

Transport Modes:
  fastmcp   - FastMCP stdio transport (for Claude Desktop integration)
  http      - HTTP REST API server (default)
  oauth     - OAuth 2.1 authenticated server with web interface
  sse       - Server-Sent Events for real-time updates

Authentication Modes:
  local     - No authentication (default for http/fastmcp)
  remote    - Token-based authentication
  multiuser - OAuth 2.1 multi-user authentication (oauth transport only)
        """,
    )

    # Transport configuration
    parser.add_argument(
        "--transport",
        choices=["fastmcp", "http", "oauth", "sse"],
        default="http",
        help="Transport mode (default: http)",
    )

    # Network configuration
    parser.add_argument(
        "--host",
        default="localhost",
        help="Server host address (default: localhost)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )

    # Authentication configuration
    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        "--local",
        action="store_true",
        help="Use local mode (no authentication)",
    )

    auth_group.add_argument(
        "--multiuser",
        action="store_true",
        help="Enable multi-user mode (requires OAuth transport)",
    )

    # OAuth configuration
    parser.add_argument(
        "--public-url",
        help="Public URL for OAuth redirects (required for OAuth mode)",
    )

    parser.add_argument(
        "--admin-token",
        help="Admin authentication token",
    )

    # Database configuration
    parser.add_argument(
        "--database",
        choices=["sqlite", "postgresql"],
        default="sqlite",
        help="Database backend for OAuth (default: sqlite)",
    )

    parser.add_argument(
        "--db-url",
        help="Database connection URL (defaults to oauth.db for SQLite)",
    )

    # Server configuration
    parser.add_argument(
        "--server-name",
        default="MCPnp Example Server",
        help="Server name for identification",
    )

    # Development options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List available tools and exit",
    )

    return parser


def configure_environment(args) -> None:
    """Configure environment variables based on command line arguments."""
    # Set transport and basic configuration
    os.environ["MCP_TRANSPORT"] = args.transport
    os.environ["MCP_HOST"] = args.host
    os.environ["MCP_PORT"] = str(args.port)

    # Set authentication mode
    if args.local:
        os.environ["MCP_MODE"] = "local"
    elif args.multiuser:
        os.environ["MCP_MODE"] = "multiuser"
        if args.transport != "oauth":
            print(
                "Warning: Multi-user mode requires OAuth transport, switching to OAuth"
            )
            os.environ["MCP_TRANSPORT"] = "oauth"
    else:
        # Default authentication mode based on transport
        if args.transport in ["fastmcp", "http"]:
            os.environ["MCP_MODE"] = "local"
        elif args.transport == "oauth":
            os.environ["MCP_MODE"] = "multiuser"

    # Set OAuth configuration
    if args.public_url:
        os.environ["MCP_PUBLIC_URL"] = args.public_url
    elif args.transport == "oauth":
        # Use default public URL for development
        os.environ["MCP_PUBLIC_URL"] = f"http://{args.host}:{args.port}"

    if args.admin_token:
        os.environ["ADMIN_TOKEN"] = args.admin_token

    # Set logging level
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"


def validate_arguments(args) -> bool:
    """Validate command line arguments and show helpful error messages."""
    # Validate OAuth requirements
    if args.transport == "oauth":
        if args.multiuser and not args.public_url and args.host == "localhost":
            print(
                "Warning: OAuth mode with localhost may not work with external clients."
            )
            print("Consider using --public-url for production deployments.")

    # Validate database URL for PostgreSQL
    if args.database == "postgresql" and not args.db_url:
        print("Error: PostgreSQL database requires --db-url parameter")
        return False

    # Validate port range
    if not 1 <= args.port <= 65535:
        print(f"Error: Port {args.port} is outside valid range (1-65535)")
        return False

    return True


def display_server_info(args, server_tools) -> None:
    """Display server configuration and available tools."""
    print("🚀 MCPnp Example Server")
    print("=" * 50)
    print(f"Transport:     {args.transport}")
    print(f"Address:       {args.host}:{args.port}")
    print(f"Auth Mode:     {os.environ.get('MCP_MODE', 'local')}")

    if args.transport == "oauth":
        public_url = os.environ.get("MCP_PUBLIC_URL", "Not configured")
        print(f"Public URL:    {public_url}")

    print(f"Server Name:   {args.server_name}")
    print()

    print("📋 Available Tools:")
    for tool_info in server_tools:
        print(f"  • {tool_info['name']:<12} - {tool_info['description']}")
    print()

    # Show usage examples based on transport mode
    if args.transport == "http":
        print("💡 Usage Examples:")
        print("  curl -X POST -H 'Content-Type: application/json' \\")
        print('    -d \'{{"jsonrpc": "2.0", "method": "tools/list", "id": 1}}\' \\')
        print(f"    http://{args.host}:{args.port}/")
        print()
        print("  curl -X POST -H 'Content-Type: application/json' \\")
        # pylint: disable=line-too-long
        print(
            '    -d \'{{"jsonrpc": "2.0", "method": "tools/call", "params": {{"name": "greet", "arguments": {{"name": "World"}}}}, "id": 2}}\' \\'
        )
        print(f"    http://{args.host}:{args.port}/")
        print()

    elif args.transport == "fastmcp":
        print("💡 FastMCP Mode:")
        print(
            "  This server is running in FastMCP mode for Claude Desktop integration."
        )
        print("  Add this server to your Claude Desktop configuration.")
        print()

    elif args.transport == "oauth":
        public_url = os.environ.get("MCP_PUBLIC_URL", f"http://{args.host}:{args.port}")
        print("💡 OAuth Mode:")
        print(f"  Authorization endpoint: {public_url}/authorize")
        print(f"  Token endpoint:         {public_url}/token")
        print(f"  User registration:      {public_url}/register_user")
        print()


def main():
    """Main entry point for the MCP server."""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Handle list-tools option
    if args.list_tools:
        print("Available MCP Tools:")
        server = MyMCPServer()
        for tool_info in server.get_available_tools():
            print(f"  {tool_info['name']:<15} {tool_info['description']}")
            schema = tool_info["inputSchema"]
            if schema["properties"]:
                print("    Parameters:")
                for param, details in schema["properties"].items():
                    required = (
                        " (required)" if param in schema["required"] else " (optional)"
                    )
                    print(f"      {param}: {details['type']}{required}")
            else:
                print("    No parameters")
            print()
        return

    # Validate arguments
    if not validate_arguments(args):
        sys.exit(1)

    # Configure environment
    configure_environment(args)

    # Create server instance
    try:
        my_server = MyMCPServer()
        server_tools = my_server.get_available_tools()
    except Exception as e:
        print(f"Error creating server: {e}")
        sys.exit(1)

    # Display server information
    display_server_info(args, server_tools)

    # Create OAuth datastore if needed
    oauth_datastore = None
    if args.transport == "oauth":
        try:
            if args.database == "postgresql" and args.db_url:

                oauth_datastore = PostgreSQLOAuthDatastore(args.db_url)
                print(f"Using PostgreSQL database: {args.db_url}")
            else:
                db_path = args.db_url or "oauth.db"
                oauth_datastore = SQLiteOAuthDatastore(db_path)
                print(f"Using SQLite database: {db_path}")
        except ImportError as e:
            print(f"Error: Database backend not available: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error setting up database: {e}")
            sys.exit(1)

    # Create and run unified server
    try:
        print("🎯 Starting server...")
        unified_server = UnifiedMCPServer(
            tool_router=my_server,
            server_name=args.server_name,
            oauth_datastore=oauth_datastore,
        )
        unified_server.run()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
