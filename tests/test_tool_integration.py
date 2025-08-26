"""
Tests for integration of decorator-based tools with UnifiedMCPServer.
"""

from mcpnp import MCPDataServer, MCPToolServer, UnifiedMCPServer, tool


class TestUnifiedServerIntegration:
    """Test integration between decorator-based tools and UnifiedMCPServer."""

    def test_server_with_tool_router(self):
        """Test that UnifiedMCPServer works with decorator-based tool router."""

        class TestToolRouter(MCPToolServer):
            @tool("test_tool", "A test tool")
            def test_tool(self, message: str) -> str:
                return f"Test: {message}"

        router = TestToolRouter()
        server = UnifiedMCPServer(tool_router=router)

        # Test that server has the tool router
        assert server.tool_router is router

        # Test that tools are available
        tools = router.get_available_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_mcp_data_server_integration(self):
        """Test MCPDataServer integration with UnifiedMCPServer."""

        class DataToolRouter(MCPDataServer):
            @tool("store", "Store data")
            def store_data_tool(self, key: str, value: str) -> str:
                self.store_data(key, value)
                return f"Stored {key}"

            @tool("retrieve", "Retrieve data")
            def retrieve_data_tool(self, key: str) -> str:
                try:
                    return self.get_data(key)
                except KeyError:
                    return "Not found"

        router = DataToolRouter()

        # Test storage functionality
        result = router.call_tool("store", {"key": "test", "value": "data"})
        assert result["status"] == "success"

        result = router.call_tool("retrieve", {"key": "test"})
        assert result["status"] == "success"
        assert result["result"] == "data"

    def test_tool_call_through_server(self):
        """Test calling tools through the tool router interface."""

        class EchoServer(MCPToolServer):
            @tool("echo", "Echo a message")
            def echo(self, message: str) -> str:
                return f"Echo: {message}"

            @tool("upper", "Convert to uppercase")
            def upper(self, text: str) -> str:
                return text.upper()

        router = EchoServer()

        # Test echo tool
        result = router.call_tool("echo", {"message": "hello"})
        assert result["status"] == "success"
        assert result["result"] == "Echo: hello"

        # Test upper tool
        result = router.call_tool("upper", {"text": "world"})
        assert result["status"] == "success"
        assert result["result"] == "WORLD"

    def test_error_handling_integration(self):
        """Test error handling in integrated environment."""

        class ErrorServer(MCPToolServer):
            @tool("divide", "Divide two numbers")
            def divide(self, a: float, b: float) -> float:
                if b == 0:
                    raise ValueError("Cannot divide by zero")
                return a / b

        router = ErrorServer()

        # Test successful division
        result = router.call_tool("divide", {"a": 10.0, "b": 2.0})
        assert result["status"] == "success"
        assert result["result"] == 5.0

        # Test division by zero
        result = router.call_tool("divide", {"a": 10.0, "b": 0.0})
        assert result["status"] == "error"
        assert "Cannot divide by zero" in result["message"]

    def test_complex_tool_scenarios(self):
        """Test complex scenarios with multiple tools and data."""

        class ComplexServer(MCPDataServer):
            @tool("calculate", "Perform calculation and store result")
            def calculate(
                self, operation: str, a: float, b: float, store_key: str = None
            ) -> float:
                if operation == "add":
                    result = a + b
                elif operation == "multiply":
                    result = a * b
                elif operation == "subtract":
                    result = a - b
                else:
                    raise ValueError(f"Unknown operation: {operation}")

                if store_key:
                    self.store_data(store_key, result)

                return result

            @tool("get_stored", "Get stored calculation result")
            def get_stored(self, key: str) -> float:
                try:
                    return float(self.get_data(key))
                except KeyError as exc:
                    raise ValueError(f"No result stored for key: {key}") from exc

            @tool("list_calculations", "List all stored calculations")
            def list_calculations(self) -> list:
                return self.list_keys()

        router = ComplexServer()

        # Test calculation with storage
        result = router.call_tool(
            "calculate",
            {"operation": "add", "a": 15.0, "b": 25.0, "store_key": "sum_result"},
        )
        assert result["status"] == "success"
        assert result["result"] == 40.0

        # Test retrieving stored result
        result = router.call_tool("get_stored", {"key": "sum_result"})
        assert result["status"] == "success"
        assert result["result"] == 40.0

        # Test listing calculations
        result = router.call_tool("list_calculations", {})
        assert result["status"] == "success"
        assert "sum_result" in result["result"]

        # Test calculation without storage
        result = router.call_tool(
            "calculate", {"operation": "multiply", "a": 6.0, "b": 7.0}
        )
        assert result["status"] == "success"
        assert result["result"] == 42.0

        # Test invalid operation
        result = router.call_tool(
            "calculate", {"operation": "invalid", "a": 1.0, "b": 2.0}
        )
        assert result["status"] == "error"
        assert "Unknown operation" in result["message"]


class TestToolValidation:
    """Test validation and schema generation."""

    def test_schema_validation(self):
        """Test that generated schemas are valid JSON Schema."""

        class ValidationServer(MCPToolServer):
            @tool("complex_params", "Tool with complex parameters")
            def complex_params(
                self,
                required_str: str,
                required_int: int,
                optional_str: str = "default",
                optional_float: float = 3.14,
                flag: bool = False,
            ) -> dict:
                return {
                    "required_str": required_str,
                    "optional_str": optional_str,
                    "required_int": required_int,
                    "optional_float": optional_float,
                    "flag": flag,
                }

        router = ValidationServer()
        tools = router.get_available_tools()
        schema = tools[0]["inputSchema"]

        # Validate schema structure
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Check required parameters
        required = schema["required"]
        assert "required_str" in required
        assert "required_int" in required
        assert "optional_str" not in required
        assert "optional_float" not in required
        assert "flag" not in required

        # Check property types
        props = schema["properties"]
        assert props["required_str"]["type"] == "string"
        assert props["optional_str"]["type"] == "string"
        assert props["required_int"]["type"] == "number"
        assert props["optional_float"]["type"] == "number"
        assert props["flag"]["type"] == "boolean"

    def test_tool_name_uniqueness(self):
        """Test that tool names within a server can be duplicated (both are registered)."""

        class DuplicateServer(MCPToolServer):
            @tool("same_name", "First tool")
            def first_tool(self) -> str:
                return "first"

            @tool("same_name", "Second tool")
            def second_tool(self) -> str:
                return "second"

        router = DuplicateServer()
        tools = router.get_available_tools()

        # Both tools are registered with the same name
        same_name_tools = [t for t in tools if t["name"] == "same_name"]
        assert len(same_name_tools) == 2

        # The last one in the _tools dict is what gets called
        result = router.call_tool("same_name", {})
        assert result["status"] == "success"
        # The last defined method should win in the _tools dict
        assert result["result"] == "second"


class TestPerformance:
    """Test performance aspects of decorator-based tools."""

    def test_tool_registration_performance(self):
        """Test that tool registration doesn't have performance issues with many tools."""
        # Create a server class with many tools defined statically
        # Note: Dynamic addition doesn't work with metaclasses, so we test static definitions

        # Create a simple server with multiple tools
        class ManyToolsServer(MCPToolServer):
            @tool("tool_1", "Tool 1")
            def tool_1(self, value: int = 1) -> int:
                return value * 2

            @tool("tool_2", "Tool 2")
            def tool_2(self, value: int = 2) -> int:
                return value * 2

            @tool("tool_3", "Tool 3")
            def tool_3(self, value: int = 3) -> int:
                return value * 2

            @tool("tool_4", "Tool 4")
            def tool_4(self, value: int = 4) -> int:
                return value * 2

            @tool("tool_5", "Tool 5")
            def tool_5(self, value: int = 5) -> int:
                return value * 2

        # This should complete quickly
        router = ManyToolsServer()
        tools = router.get_available_tools()

        assert len(tools) == 5

        # Test calling one of the tools
        result = router.call_tool("tool_3", {"value": 15})
        assert result["status"] == "success"
        assert result["result"] == 30

    def test_multiple_instances_isolation(self):
        """Test that multiple instances don't interfere with each other."""

        class CounterServer(MCPDataServer):
            def __init__(self):
                super().__init__()
                self.counter = 0

            @tool("increment", "Increment counter")
            def increment(self) -> int:
                self.counter += 1
                return self.counter

            @tool("get_count", "Get current count")
            def get_count(self) -> int:
                return self.counter

        # Create two instances
        server1 = CounterServer()
        server2 = CounterServer()

        # They should have independent state
        result1 = server1.call_tool("increment", {})
        result2 = server2.call_tool("increment", {})

        assert result1["result"] == 1
        assert result2["result"] == 1

        # Increment server1 again
        result1 = server1.call_tool("increment", {})
        assert result1["result"] == 2

        # server2 should still be at 1
        result2 = server2.call_tool("get_count", {})
        assert result2["result"] == 1
