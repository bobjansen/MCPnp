"""
Base classes for MCP tool servers with decorator-based tool registration.
"""

import inspect
from typing import Dict, Any, List
from datetime import datetime


def tool(name: str, description: str = None):
    """Decorator for registering MCP tools with automatic schema generation.

    This is a standalone decorator that can be used directly on methods.
    The metaclass will automatically collect and register these decorated methods.

    Args:
        name: Tool name
        description: Tool description (uses docstring if not provided)

    Returns:
        Decorator function that marks the method for tool registration
    """

    def decorator(func):
        # Mark the function as an MCP tool
        func.mcp_tool_name = name
        func.mcp_tool_description = description
        return func

    return decorator


class MCPToolMeta(type):
    """Metaclass that automatically collects and registers @tool decorated methods."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Initialize tool storage
        cls._tools = {}
        cls._tool_schemas = []

        # Collect tools from all methods in the class hierarchy
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if hasattr(attr, "mcp_tool_name"):
                mcs._register_tool(
                    cls, attr, attr.mcp_tool_name, attr.mcp_tool_description
                )

        return cls

    def _register_tool(cls, func, tool_name: str, description: str = None):
        """Register a single tool method."""
        # Extract parameter info from function signature
        sig = inspect.signature(func)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name != "self":
                # Map Python types to JSON Schema types
                param_type = MCPToolMeta._get_json_type(param.annotation)

                properties[param_name] = {
                    "type": param_type,
                    "description": f"{param_name} parameter",
                }

                # Check if parameter is required (no default value)
                if param.default == param.empty:
                    required.append(param_name)

        # Register the tool
        cls._tools[tool_name] = func
        cls._tool_schemas.append(
            {
                "name": tool_name,
                "description": description or func.__doc__ or f"Execute {tool_name}",
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
        )

    @staticmethod
    def _get_json_type(python_type) -> str:
        """Convert Python type annotations to JSON Schema types."""
        if python_type == int:
            return "number"
        if python_type == float:
            return "number"
        if python_type == bool:
            return "boolean"
        if python_type == list:
            return "array"
        if python_type == dict:
            return "object"
        return "string"


class MCPToolServer(metaclass=MCPToolMeta):
    """Base class for MCP servers with automatic decorator-based tool registration.

    Users can inherit from this class and use the @tool decorator directly on methods.
    Tools are automatically registered via metaclass magic - no __init__ needed!

    Example:
        from mcpnp import MCPToolServer, tool

        class MyServer(MCPToolServer):
            @tool("greet", "Greet someone")
            def greet(self, name: str) -> str:
                return f"Hello, {name}!"

            @tool("add", "Add numbers")
            def add(self, a: float, b: float) -> float:
                return a + b
    """

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools with their schemas.

        This method is required by the UnifiedMCPServer.
        """
        return self._tool_schemas

    def call_tool(
        self, tool_name: str, arguments: Dict[str, Any], manager=None
    ) -> Dict[str, Any]:
        """Route tool call to appropriate implementation.

        This method is required by the UnifiedMCPServer.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            manager: Optional manager instance for authenticated tools

        Returns:
            Tool execution result in MCP format
        """
        try:
            if tool_name not in self._tools:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}

            func = self._tools[tool_name]
            # Call the method on this instance
            result = func(self, **arguments)

            # Ensure result is in proper MCP format
            if isinstance(result, dict) and "status" in result:
                return result
            return {
                "status": "success",
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "message": f"Tool execution failed: {str(e)}"}


class MCPDataServer(MCPToolServer):
    """Extended base class with built-in data storage capabilities.

    Provides a simple in-memory key-value store that tool methods can use.
    """

    def __init__(self):
        super().__init__()
        self.data_store = {}

    def store_data(self, key: str, value: Any) -> Dict[str, Any]:
        """Store data with metadata."""
        self.data_store[key] = {"value": value, "stored_at": datetime.now().isoformat()}
        return {"key": key, "stored_at": self.data_store[key]["stored_at"]}

    def get_data(self, key: str) -> Any:
        """Retrieve stored data."""
        if key not in self.data_store:
            raise KeyError(f"Key '{key}' not found")
        return self.data_store[key]["value"]

    def list_keys(self) -> List[str]:
        """List all stored keys."""
        return list(self.data_store.keys())

    def delete_data(self, key: str) -> bool:
        """Delete stored data."""
        if key in self.data_store:
            del self.data_store[key]
            return True
        return False
