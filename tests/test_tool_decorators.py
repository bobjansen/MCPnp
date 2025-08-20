"""
Tests for MCP tool decorators and base classes.
"""

import pytest
from typing import List, Dict, Any
from mcpnp.tools.base import MCPToolServer, MCPDataServer, tool


class TestToolDecorator:
    """Test the @tool decorator functionality."""

    def test_tool_decorator_marks_function(self):
        """Test that @tool decorator properly marks functions."""

        @tool("test_tool", "A test tool")
        def test_func():
            return "test"

        assert hasattr(test_func, "mcp_tool_name")
        assert hasattr(test_func, "mcp_tool_description")
        assert test_func.mcp_tool_name == "test_tool"
        assert test_func.mcp_tool_description == "A test tool"

    def test_tool_decorator_without_description(self):
        """Test @tool decorator with only name."""

        @tool("simple_tool")
        def simple_func():
            return "simple"

        assert simple_func.mcp_tool_name == "simple_tool"
        assert simple_func.mcp_tool_description is None


class TestMCPToolServer:
    """Test the MCPToolServer base class."""

    def test_empty_server_has_no_tools(self):
        """Test that empty server has no tools."""

        class EmptyServer(MCPToolServer):
            pass

        server = EmptyServer()
        assert server.get_available_tools() == []

    def test_server_with_decorated_methods(self):
        """Test server with @tool decorated methods."""

        class TestServer(MCPToolServer):
            @tool("greet", "Greet someone")
            def greet(self, name: str) -> str:
                return f"Hello, {name}!"

            @tool("add", "Add two numbers")
            def add_numbers(self, a: float, b: float) -> float:
                return a + b

        server = TestServer()
        tools = server.get_available_tools()

        assert len(tools) == 2

        # Check greet tool
        greet_tool = next(t for t in tools if t["name"] == "greet")
        assert greet_tool["description"] == "Greet someone"
        assert greet_tool["inputSchema"]["type"] == "object"
        assert "name" in greet_tool["inputSchema"]["properties"]
        assert greet_tool["inputSchema"]["properties"]["name"]["type"] == "string"
        assert "name" in greet_tool["inputSchema"]["required"]

        # Check add tool
        add_tool = next(t for t in tools if t["name"] == "add")
        assert add_tool["description"] == "Add two numbers"
        assert "a" in add_tool["inputSchema"]["properties"]
        assert "b" in add_tool["inputSchema"]["properties"]
        assert add_tool["inputSchema"]["properties"]["a"]["type"] == "number"
        assert add_tool["inputSchema"]["properties"]["b"]["type"] == "number"

    def test_tool_type_mapping(self):
        """Test that Python types are correctly mapped to JSON Schema types."""

        class TypeTestServer(MCPToolServer):
            @tool("type_test", "Test different types")
            def type_test(
                self,
                text: str,
                number: int,
                decimal: float,
                flag: bool,
                items: list,
                data: dict,
            ) -> str:
                return "types tested"

        server = TypeTestServer()
        tools = server.get_available_tools()
        tool_schema = tools[0]["inputSchema"]["properties"]

        assert tool_schema["text"]["type"] == "string"
        assert tool_schema["number"]["type"] == "number"
        assert tool_schema["decimal"]["type"] == "number"
        assert tool_schema["flag"]["type"] == "boolean"
        assert tool_schema["items"]["type"] == "array"
        assert tool_schema["data"]["type"] == "object"

    def test_optional_parameters(self):
        """Test that optional parameters are not in required list."""

        class OptionalServer(MCPToolServer):
            @tool("optional_test", "Test optional parameters")
            def optional_test(self, required: str, optional: str = "default") -> str:
                return f"{required} {optional}"

        server = OptionalServer()
        tools = server.get_available_tools()
        schema = tools[0]["inputSchema"]

        assert "required" in schema["required"]
        assert "optional" not in schema["required"]
        assert "optional" in schema["properties"]

    def test_call_tool_success(self):
        """Test successful tool calls."""

        class CallTestServer(MCPToolServer):
            @tool("echo", "Echo a message")
            def echo(self, message: str) -> str:
                return f"Echo: {message}"

            @tool("multiply", "Multiply two numbers")
            def multiply(self, a: float, b: float) -> float:
                return a * b

        server = CallTestServer()

        # Test echo tool
        result = server.call_tool("echo", {"message": "hello"})
        assert result["status"] == "success"
        assert result["result"] == "Echo: hello"
        assert "timestamp" in result

        # Test multiply tool
        result = server.call_tool("multiply", {"a": 3.5, "b": 2.0})
        assert result["status"] == "success"
        assert result["result"] == 7.0

    def test_call_unknown_tool(self):
        """Test calling unknown tool returns error."""

        class SimpleServer(MCPToolServer):
            @tool("test", "Test tool")
            def test_tool(self) -> str:
                return "test"

        server = SimpleServer()
        result = server.call_tool("unknown", {})

        assert result["status"] == "error"
        assert "Unknown tool: unknown" in result["message"]

    def test_call_tool_with_exception(self):
        """Test that tool exceptions are handled properly."""

        class ErrorServer(MCPToolServer):
            @tool("error_tool", "A tool that raises an error")
            def error_tool(self) -> str:
                raise ValueError("Something went wrong")

        server = ErrorServer()
        result = server.call_tool("error_tool", {})

        assert result["status"] == "error"
        assert "Tool execution failed" in result["message"]
        assert "Something went wrong" in result["message"]

    def test_tool_with_dict_result_status(self):
        """Test tool that returns dict with status is passed through."""

        class StatusServer(MCPToolServer):
            @tool("status_tool", "Tool that returns status dict")
            def status_tool(self) -> Dict[str, Any]:
                return {"status": "custom", "data": "test", "code": 200}

        server = StatusServer()
        result = server.call_tool("status_tool", {})

        assert result["status"] == "custom"
        assert result["data"] == "test"
        assert result["code"] == 200
        assert "timestamp" not in result  # Should not add timestamp for status dicts


class TestMCPDataServer:
    """Test the MCPDataServer extended class."""

    def test_data_server_has_storage(self):
        """Test that MCPDataServer has data storage capabilities."""
        server = MCPDataServer()

        # Test storing data
        result = server.store_data("test_key", "test_value")
        assert result["key"] == "test_key"
        assert "stored_at" in result

        # Test retrieving data
        value = server.get_data("test_key")
        assert value == "test_value"

        # Test listing keys
        keys = server.list_keys()
        assert "test_key" in keys

        # Test deleting data
        deleted = server.delete_data("test_key")
        assert deleted is True

        # Test key no longer exists
        with pytest.raises(KeyError):
            server.get_data("test_key")

    def test_data_server_with_tools(self):
        """Test MCPDataServer with tool methods."""

        class DataTestServer(MCPDataServer):
            @tool("store_item", "Store an item")
            def store_item(self, key: str, value: str) -> str:
                self.store_data(key, value)
                return f"Stored {key}"

            @tool("get_item", "Get an item")
            def get_item(self, key: str) -> str:
                try:
                    return self.get_data(key)
                except KeyError:
                    return f"Key {key} not found"

            @tool("list_items", "List all items")
            def list_items(self) -> List[str]:
                return self.list_keys()

        server = DataTestServer()

        # Test storing via tool
        result = server.call_tool("store_item", {"key": "test", "value": "data"})
        assert result["status"] == "success"
        assert result["result"] == "Stored test"

        # Test retrieving via tool
        result = server.call_tool("get_item", {"key": "test"})
        assert result["status"] == "success"
        assert result["result"] == "data"

        # Test listing via tool
        result = server.call_tool("list_items", {})
        assert result["status"] == "success"
        assert "test" in result["result"]

        # Test getting non-existent key
        result = server.call_tool("get_item", {"key": "missing"})
        assert result["status"] == "success"
        assert "not found" in result["result"]


class TestInheritance:
    """Test inheritance behavior with decorated tools."""

    def test_inheritance_collects_parent_tools(self):
        """Test that child classes inherit parent tools."""

        class ParentServer(MCPToolServer):
            @tool("parent_tool", "Tool from parent")
            def parent_tool(self) -> str:
                return "parent"

        class ChildServer(ParentServer):
            @tool("child_tool", "Tool from child")
            def child_tool(self) -> str:
                return "child"

        server = ChildServer()
        tools = server.get_available_tools()
        tool_names = [t["name"] for t in tools]

        assert len(tools) == 2
        assert "parent_tool" in tool_names
        assert "child_tool" in tool_names

    def test_multiple_inheritance(self):
        """Test multiple inheritance with tool collection."""

        class MixinA(MCPToolServer):
            @tool("tool_a", "Tool from mixin A")
            def tool_a(self) -> str:
                return "a"

        class MixinB(MCPToolServer):
            @tool("tool_b", "Tool from mixin B")
            def tool_b(self) -> str:
                return "b"

        class CombinedServer(MixinA, MixinB):
            @tool("tool_c", "Tool from combined")
            def tool_c(self) -> str:
                return "c"

        server = CombinedServer()
        tools = server.get_available_tools()
        tool_names = [t["name"] for t in tools]

        assert len(tools) == 3
        assert "tool_a" in tool_names
        assert "tool_b" in tool_names
        assert "tool_c" in tool_names


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_no_init_method_needed(self):
        """Test that no __init__ method is required."""

        class NoInitServer(MCPToolServer):
            @tool("test", "Test tool")
            def test_method(self) -> str:
                return "works"

        # Should work without any __init__ method
        server = NoInitServer()
        assert len(server.get_available_tools()) == 1

        result = server.call_tool("test", {})
        assert result["status"] == "success"
        assert result["result"] == "works"

    def test_method_without_type_hints(self):
        """Test methods without type hints default to string."""

        class NoHintsServer(MCPToolServer):
            @tool("no_hints", "Tool without type hints")
            def no_hints_method(self, param):
                return f"Got: {param}"

        server = NoHintsServer()
        tools = server.get_available_tools()

        param_type = tools[0]["inputSchema"]["properties"]["param"]["type"]
        assert param_type == "string"

    def test_method_with_docstring_description(self):
        """Test that docstring is used when no description provided."""

        class DocstringServer(MCPToolServer):
            @tool("docstring_tool")
            def docstring_method(self) -> str:
                """This is the docstring description."""
                return "test"

        server = DocstringServer()
        tools = server.get_available_tools()

        assert tools[0]["description"] == "This is the docstring description."

    def test_method_without_description_or_docstring(self):
        """Test fallback description when none provided."""

        class NoDescServer(MCPToolServer):
            @tool("no_desc_tool")
            def no_desc_method(self) -> str:
                return "test"

        server = NoDescServer()
        tools = server.get_available_tools()

        assert tools[0]["description"] == "Execute no_desc_tool"
