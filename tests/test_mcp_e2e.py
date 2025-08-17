#!/usr/bin/env python3
"""
End-to-End tests for MCP server using the actual MCP protocol.
These tests simulate real Claude Desktop interactions through the MCP protocol.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
import pytest

# Import the MCP server directly for protocol testing
from mcpnp.server import UnifiedMCPServer
from mcp_tool_router import MCPToolRouter

from .conftest import cleanup_test_environment

# Project root for subprocess calls
project_root = Path(__file__).parent.parent.parent


class TestMCPE2E:
    """End-to-End tests for MCP server protocol."""

    @pytest.fixture
    def server_process(self):
        """Start MCP server process for testing."""
        # Set up environment
        env = os.environ.copy()

        # Start server process
        cmd = [sys.executable, "-m", "uv", "run", "server.py"]
        with subprocess.Popen(
            cmd,
            env=env,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:

            # Wait for server to start
            time.sleep(2)

            yield process

            # Cleanup
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    def test_server_startup(self):
        """Test that server starts up correctly."""
        env = os.environ.copy()

        # Start server with timeout
        cmd = [
            sys.executable,
            "-c",
            f"""
import sys
sys.path.insert(0, '{project_root}')
from run_mcp import main
try:
    main()
except KeyboardInterrupt:
    pass
""",
        ]

        with subprocess.Popen(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:

            # Let it run briefly then stop
            time.sleep(1)
            process.terminate()
            _, stderr = process.communicate(timeout=5)

            # Check that it started without critical errors
            stderr_text = stderr.decode()
            assert "Error" not in stderr_text or "import" not in stderr_text.lower()

    def test_fastmcp_mode(self):
        """Test FastMCP transport mode."""
        env = os.environ.copy()
        env["MCP_TRANSPORT"] = "fastmcp"

        # Test FastMCP server initialization
        cmd = [
            sys.executable,
            "-c",
            f"""
import sys
sys.path.insert(0, '{project_root}')
from mcpnp.server import UnifiedMCPServer

try:
    # Test that FastMCP server can be created successfully
    server = UnifiedMCPServer()
    print("FastMCP server initialized successfully")
    print(f"Transport: {{server.transport}}")
    print(f"Auth mode: {{server.auth_mode}}")

    # Test that it has the expected components
    if hasattr(server, 'mcp') and server.mcp is not None:
        print("FastMCP component initialized")
except (ImportError, ValueError, TypeError, RuntimeError) as e:
    print(f"Error initializing FastMCP server: {{e}}")
    import traceback
    traceback.print_exc()
""",
        ]

        with subprocess.Popen(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:

            stdout, stderr = process.communicate(timeout=10)

            # Check output for success indicators
            output = stdout.decode() + stderr.decode()
            assert "initialized successfully" in output
            assert "FastMCP component initialized" in output

    def test_mcp_protocol_flow(self):
        """Test complete MCP protocol communication flow."""
        # This simulates the MCP protocol handshake and tool calls

        # Use our stub router for testing
        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        # Test tool listing
        available_tools = server.tool_router.get_available_tools()
        assert len(available_tools) > 0

        # Test tool call flow
        tool_call_result = server.tool_router.call_tool("ping", {}, None)
        assert tool_call_result["status"] == "success"
        assert tool_call_result["message"] == "pong"

        # Test another tool call with parameters
        echo_result = server.tool_router.call_tool(
            "echo", {"message": "test message"}, None
        )
        assert echo_result["status"] == "success"
        assert echo_result["echo"] == "test message"

    def test_error_recovery(self):
        """Test error recovery and resilience."""

        # Use our stub router for testing
        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        # Test invalid tool
        result = server.tool_router.call_tool("invalid_tool_name", {}, None)
        assert result["status"] == "error"
        assert "unknown tool" in result["message"].lower()

        # Test simulated error
        error_result = server.tool_router.call_tool(
            "simulate_error", {"error_type": "ValueError"}, None
        )
        assert error_result["status"] == "error"
        assert "tool execution failed" in error_result["message"].lower()

        # Test malformed arguments
        result = server.tool_router.call_tool(
            "validate_params", {"invalid_field": "value"}, None
        )
        assert result["status"] == "error"

        # Test that server is still functional after errors
        result = server.tool_router.call_tool("ping", {}, None)
        assert result["status"] == "success"

    def test_concurrent_operations(self):
        """Test concurrent tool operations."""

        # Use our stub router for testing
        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        results = []

        def call_tool_thread(tool_name, args, thread_id):
            try:
                result = server.tool_router.call_tool(tool_name, args, None)
                results.append((thread_id, result))
            except (ValueError, TypeError, RuntimeError) as e:
                results.append((thread_id, {"status": "error", "message": str(e)}))

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=call_tool_thread, args=("list_items", {}, i)
            )
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(results) == 5
        for _, result in results:
            assert result["status"] == "success"

    def test_data_persistence(self):
        """Test that data persists within the same session."""

        # First server instance - add data
        tool_router1 = MCPToolRouter()
        server1 = UnifiedMCPServer(tool_router=tool_router1)

        # Add some test data
        result1 = server1.tool_router.call_tool(
            "add_item", {"name": "test_item", "quantity": 5}, None
        )
        assert result1["status"] == "success"

        result2 = server1.tool_router.call_tool(
            "increment_counter", {"amount": 10}, None
        )
        assert result2["status"] == "success"

        # Check data exists
        items_result = server1.tool_router.call_tool("list_items", {}, None)
        assert items_result["status"] == "success"
        assert "test_item" in items_result["items"]
        assert items_result["items"]["test_item"] == 5

        counter_result = server1.tool_router.call_tool("get_counter", {}, None)
        assert counter_result["status"] == "success"
        assert counter_result["counter"] == 10

        # Test data consistency within same router instance
        result3 = server1.tool_router.call_tool(
            "add_item", {"name": "test_item", "quantity": 3}, None
        )
        assert result3["status"] == "success"

        items_result2 = server1.tool_router.call_tool("list_items", {}, None)
        assert items_result2["items"]["test_item"] == 8  # Should be 5 + 3

    def teardown_method(self):
        """Clean up after each test."""
        cleanup_test_environment()


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance."""

    def test_tool_schema_compliance(self):
        """Test that tool schemas comply with MCP standard."""

        router = MCPToolRouter()
        tools = router.get_available_tools()

        for tool in tools:
            # Required fields
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

            # Schema structure
            schema = tool["inputSchema"]
            assert "type" in schema
            assert schema["type"] == "object"
            assert "properties" in schema

            # Note: 'required' is optional in our stub implementation
            for prop_name, prop_def in schema["properties"].items():
                assert "type" in prop_def
                # Description is not required for array types (they use items structure)
                if prop_def.get("type") != "array":
                    assert (
                        "description" in prop_def
                    ), f"Property {prop_name} missing description: {prop_def}"

    def test_response_format_compliance(self):
        """Test that responses comply with expected format."""

        # Use our stub router for testing
        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        # Test various tool responses
        tools_to_test = [
            ("ping", {}),
            ("list_items", {}),
            ("get_counter", {}),
        ]

        for tool_name, args in tools_to_test:
            result = server.tool_router.call_tool(tool_name, args, None)

            # All responses should have status
            assert "status" in result
            assert result["status"] in ["success", "error"]

            # Error responses should have message
            if result["status"] == "error":
                assert "message" in result


if __name__ == "__main__":
    # Run tests directly if called as script
    pytest.main([__file__, "-v", "--tb=short"])
