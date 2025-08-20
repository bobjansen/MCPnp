"""
MCP Server Example
"""

import os
from typing import List
from mcpnp import UnifiedMCPServer, MCPDataServer, tool


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


def main():
    """Run the MCP server."""
    # Set transport mode
    os.environ["MCP_TRANSPORT"] = "http"
    os.environ["MCP_HOST"] = "localhost"
    os.environ["MCP_PORT"] = "8000"

    print("Starting MCP Server Example...")

    my_server = MyMCPServer()

    print("Available tools:")
    for tool_info in my_server.get_available_tools():
        print(f"  - {tool_info['name']}: {tool_info['description']}")
    print()

    # Create and run unified server
    unified_server = UnifiedMCPServer(tool_router=my_server)
    unified_server.run()


if __name__ == "__main__":
    main()
