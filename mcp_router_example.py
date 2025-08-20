"""
Simple MCP Tool Router Example - Self-contained and general purpose
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPToolRouter:
    """Simple MCP tool router with example tools."""

    def __init__(self):
        self.data_store = {}  # Simple in-memory storage

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools with their schemas."""
        return [
            {
                "name": "echo",
                "description": "Echo back the provided message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"}
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "add_data",
                "description": "Store a key-value pair",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Storage key"},
                        "value": {"type": "string", "description": "Value to store"},
                    },
                    "required": ["key", "value"],
                },
            },
            {
                "name": "get_data",
                "description": "Retrieve a value by key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Storage key"}
                    },
                    "required": ["key"],
                },
            },
            {
                "name": "list_data",
                "description": "List all stored keys",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "calculate",
                "description": "Perform basic arithmetic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                        },
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["operation", "a", "b"],
                },
            },
        ]

    def call_tool(
        self, tool_name: str, arguments: Dict[str, Any], manager=None
    ) -> Dict[str, Any]:
        """Route tool call to appropriate implementation."""
        try:
            if tool_name == "echo":
                return self._echo(arguments)
            if tool_name == "add_data":
                return self._add_data(arguments)
            if tool_name == "get_data":
                return self._get_data(arguments)
            if tool_name == "list_data":
                return self._list_data(arguments)
            if tool_name == "calculate":
                return self._calculate(arguments)
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error in tool '{tool_name}': {str(e)}")
            return {"status": "error", "message": f"Tool execution failed: {str(e)}"}

    def _echo(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Echo back the provided message."""
        message = arguments.get("message", "")
        return {
            "status": "success",
            "message": f"Echo: {message}",
            "timestamp": datetime.now().isoformat(),
        }

    def _add_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Store a key-value pair."""
        key = arguments.get("key")
        value = arguments.get("value")

        if not key or not value:
            return {"status": "error", "message": "Both key and value are required"}

        self.data_store[key] = {"value": value, "created": datetime.now().isoformat()}

        return {
            "status": "success",
            "message": f"Stored '{key}' successfully",
            "key": key,
            "value": value,
        }

    def _get_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve a value by key."""
        key = arguments.get("key")

        if not key:
            return {"status": "error", "message": "Key is required"}

        if key not in self.data_store:
            return {"status": "error", "message": f"Key '{key}' not found"}

        data = self.data_store[key]
        return {
            "status": "success",
            "key": key,
            "value": data["value"],
            "created": data["created"],
        }

    def _list_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List all stored keys."""
        keys = list(self.data_store.keys())
        return {"status": "success", "keys": keys, "count": len(keys)}

    def _calculate(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic arithmetic operations."""
        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")

        if a is None or b is None:
            return {"status": "error", "message": "Both numbers a and b are required"}

        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return {"status": "error", "message": "Division by zero"}
                result = a / b
            else:
                return {"status": "error", "message": "Invalid operation"}

            return {
                "status": "success",
                "operation": operation,
                "a": a,
                "b": b,
                "result": result,
            }
        except Exception as e:
            return {"status": "error", "message": f"Calculation failed: {str(e)}"}


def main():
    # Example usage
    router = MCPToolRouter()

    # Test echo tool
    result = router.call_tool("echo", {"message": "Hello, World!"})
    print("Echo result:", result)

    # Test data storage
    router.call_tool("add_data", {"key": "test", "value": "example value"})
    result = router.call_tool("get_data", {"key": "test"})
    print("Data retrieval:", result)

    # Test calculation
    result = router.call_tool("calculate", {"operation": "add", "a": 5, "b": 3})
    print("Calculation result:", result)

    # List available tools
    tools = router.get_available_tools()
    print(f"Available tools: {[tool['name'] for tool in tools]}")


if __name__ == "__main__":
    main()
