#!/usr/bin/env python3
"""
MCP Server Launcher - Unified interface for all MCP server modes.

Usage:
    python run_mcp.py [mode] [options]

Modes:
    fastmcp     - FastMCP server (stdio) - default
    http        - HTTP REST API server
    oauth       - OAuth 2.1 authenticated server
    sse         - Server-Sent Events server

Options:
    --host HOST     - Server host (default: localhost)
    --port PORT     - Server port (default: 8000)
    --local         - Local mode (no authentication)
    --multiuser     - Multi-user mode (OAuth required)

Examples:
    python run_mcp.py                          # FastMCP local mode
    python run_mcp.py http --port 8000         # HTTP server on port 8000
    python run_mcp.py oauth --multiuser        # OAuth multi-user server
"""

import os
import sys
import argparse
from mcpnp.server import UnifiedMCPServer
from mcpnp.auth.datastore_sqlite import SQLiteOAuthDatastore
from mcpnp.auth.datastore_postgresql import PostgreSQLOAuthDatastore


def main():
    """Run the MCP server"""
    parser = argparse.ArgumentParser(
        description="MCPnp Unified Server Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "transport",
        nargs="?",
        default="fastmcp",
        choices=["fastmcp", "http", "oauth", "sse"],
        help="Transport mode (default: fastmcp)",
    )

    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")

    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument("--local", action="store_true", help="Local mode (no auth)")
    auth_group.add_argument(
        "--multiuser", action="store_true", help="Multi-user mode (OAuth)"
    )

    parser.add_argument(
        "--backend", choices=["sqlite", "postgresql"], help="Database backend"
    )
    parser.add_argument("--db-url", help="Database connection URL")

    args = parser.parse_args()

    # Set environment variables based on arguments
    os.environ["MCP_TRANSPORT"] = args.transport
    os.environ["MCP_HOST"] = args.host
    os.environ["MCP_PORT"] = str(args.port)

    # Set auth mode
    if args.local:
        os.environ["MCP_MODE"] = "local"
    elif args.multiuser:
        os.environ["MCP_MODE"] = "multiuser"
        if args.transport != "oauth":
            print(
                "Warning: Multi-user mode requires OAuth transport, switching to OAuth"
            )
            os.environ["MCP_TRANSPORT"] = "oauth"

    # Import after environment is set

    # Create OAuth datastore if needed
    oauth_datastore = None
    if args.transport == "oauth" or os.environ.get("MCP_TRANSPORT") == "oauth":
        if args.backend == "postgresql" and args.db_url:
            oauth_datastore = PostgreSQLOAuthDatastore(args.db_url)
        else:
            # Default to SQLite
            db_path = args.db_url or "oauth.db"
            oauth_datastore = SQLiteOAuthDatastore(db_path)

        print(f"  Database: {oauth_datastore.__class__.__name__}")

    # Create and run server
    print("Starting MCPnp server:")
    print(f"  Transport: {args.transport}")
    print(f"  Auth Mode: {os.environ.get('MCP_MODE', 'local')}")
    print(f"  Address: {args.host}:{args.port}")
    print()

    try:
        server = UnifiedMCPServer(oauth_datastore=oauth_datastore)
        server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
