"""
Tests for the example server using decorator-based tools.
"""

from mcpnp import UnifiedMCPServer, MCPDataServer, tool


class ExampleMCPServer(MCPDataServer):
    """Example MCP server for testing the decorator approach."""

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
    def list_stored_keys(self) -> list:
        """List all stored keys."""
        return self.list_keys()

    @tool("delete", "Delete a stored value")
    def delete_value(self, key: str) -> str:
        """Delete a stored value."""
        if self.delete_data(key):
            return f"Deleted '{key}' successfully"
        return f"Key '{key}' not found"


class TestExampleServer:
    """Test the complete example server."""

    def test_example_server_creation(self):
        """Test that the example server can be created without errors."""
        server = ExampleMCPServer()
        assert server is not None

        # Check that all expected tools are registered
        tools = server.get_available_tools()
        tool_names = [t["name"] for t in tools]

        expected_tools = [
            "greet",
            "add",
            "multiply",
            "store",
            "retrieve",
            "list_keys",
            "delete",
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names

    def test_unified_server_integration(self):
        """Test that the example server works with UnifiedMCPServer."""
        example_server = ExampleMCPServer()
        unified_server = UnifiedMCPServer(tool_router=example_server)

        assert unified_server.tool_router is example_server

    def test_greet_tool(self):
        """Test the greet tool functionality."""
        server = ExampleMCPServer()

        # Test with default greeting
        result = server.call_tool("greet", {"name": "World"})
        assert result["status"] == "success"
        assert result["result"] == "Hello, World! Welcome to MCPnp!"

        # Test with custom greeting
        result = server.call_tool("greet", {"name": "Developer", "greeting": "Hi"})
        assert result["status"] == "success"
        assert result["result"] == "Hi, Developer! Welcome to MCPnp!"

    def test_math_tools(self):
        """Test the mathematical tools."""
        server = ExampleMCPServer()

        # Test addition
        result = server.call_tool("add", {"a": 15.5, "b": 24.5})
        assert result["status"] == "success"
        assert result["result"] == 40.0

        # Test multiplication
        result = server.call_tool("multiply", {"a": 6.0, "b": 7.0})
        assert result["status"] == "success"
        assert result["result"] == 42.0

        # Test with integers
        result = server.call_tool("add", {"a": 10, "b": 5})
        assert result["status"] == "success"
        assert result["result"] == 15

    def test_data_storage_workflow(self):
        """Test the complete data storage workflow."""
        server = ExampleMCPServer()

        # Initially, no keys should exist
        result = server.call_tool("list_keys", {})
        assert result["status"] == "success"
        assert result["result"] == []

        # Store some data
        result = server.call_tool("store", {"key": "test_key", "value": "test_value"})
        assert result["status"] == "success"
        assert "Stored 'test_key' successfully" in result["result"]

        # Retrieve the data
        result = server.call_tool("retrieve", {"key": "test_key"})
        assert result["status"] == "success"
        assert result["result"] == "test_value"

        # List keys should now show our key
        result = server.call_tool("list_keys", {})
        assert result["status"] == "success"
        assert "test_key" in result["result"]

        # Store another piece of data
        result = server.call_tool(
            "store", {"key": "another_key", "value": "another_value"}
        )
        assert result["status"] == "success"

        # List should show both keys
        result = server.call_tool("list_keys", {})
        assert result["status"] == "success"
        assert len(result["result"]) == 2
        assert "test_key" in result["result"]
        assert "another_key" in result["result"]

        # Delete a key
        result = server.call_tool("delete", {"key": "test_key"})
        assert result["status"] == "success"
        assert "Deleted 'test_key' successfully" in result["result"]

        # Try to retrieve deleted key
        result = server.call_tool("retrieve", {"key": "test_key"})
        assert result["status"] == "success"
        assert "not found" in result["result"]

        # Delete non-existent key
        result = server.call_tool("delete", {"key": "non_existent"})
        assert result["status"] == "success"
        assert "not found" in result["result"]

    def test_tool_schemas(self):
        """Test that tool schemas are correctly generated."""
        server = ExampleMCPServer()
        tools = server.get_available_tools()

        # Find the greet tool
        greet_tool = next(t for t in tools if t["name"] == "greet")
        schema = greet_tool["inputSchema"]

        # Check schema structure
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Check properties
        props = schema["properties"]
        assert "name" in props
        assert "greeting" in props
        assert props["name"]["type"] == "string"
        assert props["greeting"]["type"] == "string"

        # Check required parameters
        assert "name" in schema["required"]
        assert "greeting" not in schema["required"]  # Has default value

        # Find the add tool
        add_tool = next(t for t in tools if t["name"] == "add")
        add_schema = add_tool["inputSchema"]

        # Check math tool schema
        add_props = add_schema["properties"]
        assert "a" in add_props
        assert "b" in add_props
        assert add_props["a"]["type"] == "number"
        assert add_props["b"]["type"] == "number"
        assert "a" in add_schema["required"]
        assert "b" in add_schema["required"]

    def test_error_handling(self):
        """Test error handling in the example server."""
        server = ExampleMCPServer()

        # Test calling unknown tool
        result = server.call_tool("unknown_tool", {})
        assert result["status"] == "error"
        assert "Unknown tool" in result["message"]

        # Test tool with missing required parameter
        # This would normally be caught by the MCP protocol layer,
        # but let's test the tool execution directly
        result = server.call_tool("greet", {})
        assert result["status"] == "error"
        assert "Tool execution failed" in result["message"]

    def test_instance_isolation(self):
        """Test that multiple server instances don't interfere."""
        server1 = ExampleMCPServer()
        server2 = ExampleMCPServer()

        # Store data in server1
        server1.call_tool("store", {"key": "server1_key", "value": "server1_value"})

        # Store data in server2
        server2.call_tool("store", {"key": "server2_key", "value": "server2_value"})

        # Check that server1 only has its data
        result1 = server1.call_tool("list_keys", {})
        assert "server1_key" in result1["result"]
        assert "server2_key" not in result1["result"]

        # Check that server2 only has its data
        result2 = server2.call_tool("list_keys", {})
        assert "server2_key" in result2["result"]
        assert "server1_key" not in result2["result"]
