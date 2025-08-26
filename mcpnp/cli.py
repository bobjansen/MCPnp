#!/usr/bin/env python3
"""MCPnp CLI - Command line interface for MCPnp framework.

Provides utilities for working with MCPnp servers and tools.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from run_mcp import main as server_main


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCPnp - Model Context Protocol framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Version command
    subparsers.add_parser("version", help="Show version information")

    # Server command
    server_parser = subparsers.add_parser("server", help="Start MCP server")
    server_parser.add_argument(
        "transport",
        nargs="?",
        default="fastmcp",
        choices=["fastmcp", "http", "oauth", "sse"],
        help="Transport mode (default: fastmcp)",
    )
    server_parser.add_argument("--host", default="localhost", help="Server host")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    server_parser.add_argument("--local", action="store_true", help="Local mode")
    server_parser.add_argument(
        "--multiuser", action="store_true", help="Multi-user mode"
    )

    # Check command
    check_parser = subparsers.add_parser("check", help="Run code quality checks")
    check_parser.add_argument("--fix", action="store_true", help="Apply fixes")
    check_parser.add_argument("--quick", action="store_true", help="Quick check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "version":
        print("MCPnp 1.0.0")
        print("Model Context Protocol framework")
        return 0

    if args.command == "server":
        # Set up sys.argv for run_mcp
        sys.argv = ["mcpnp", args.transport]
        if args.host != "localhost":
            sys.argv.extend(["--host", args.host])
        if args.port != 8000:
            sys.argv.extend(["--port", str(args.port)])
        if args.local:
            sys.argv.append("--local")
        if args.multiuser:
            sys.argv.append("--multiuser")
        return server_main()

    if args.command == "check":
        # Run quality checks
        check_script = Path(__file__).parent.parent / "check.py"
        if not check_script.exists():
            print("Error: check.py not found", file=sys.stderr)
            return 1

        cmd = [sys.executable, str(check_script)]
        if args.fix:
            cmd.append("--fix")
        if args.quick:
            cmd.append("--quick")

        return subprocess.call(cmd)

    return 0


if __name__ == "__main__":
    sys.exit(main())
