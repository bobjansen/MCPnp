"""MCPnp - Model Context Protocol, no problem.

A standalone, reusable package for building MCP servers with multiple transport modes,
authentication systems, and user management capabilities.
"""

from .auth.user_manager import UserManager
from .server.context import MCPContext
from .server.unified_server import UnifiedMCPServer
from .tools.base import MCPDataServer, MCPToolServer, tool

__version__ = "1.0.0"

__all__ = [
    "MCPContext",
    "MCPDataServer",
    "MCPToolServer",
    "UnifiedMCPServer",
    "UserManager",
    "tool",
]
