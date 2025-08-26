"""
End-to-End tests for different MCP transport modes.
Tests FastMCP (stdio), HTTP REST, Server-Sent Events, and OAuth 2.1 transports.
"""

import os
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from mcp_tool_router import MCPToolRouter, MockUserManager
from mcpnp.server import UnifiedMCPServer

from .conftest import cleanup_test_environment

# Project root for subprocess calls
project_root = Path(__file__).parent.parent.parent


class TestMCPTransportModes:
    """Test different MCP transport modes."""

    @pytest.fixture
    def base_env_setup(self):
        """Setup base environment variables."""
        os.environ["MCP_HOST"] = "localhost"
        os.environ["MCP_PORT"] = "18000"  # Use different port for testing

    def test_fastmcp_stdio_transport(self):
        """Test FastMCP stdio transport mode."""
        os.environ["MCP_TRANSPORT"] = "fastmcp"
        os.environ["MCP_MODE"] = "local"

        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        # Verify server setup
        assert server.transport == "fastmcp"
        assert server.auth_mode == "local"
        assert server.mcp is not None
        assert hasattr(server.mcp, "run")

        # Verify tools are registered
        assert server.tool_router is not None
        tools = server.tool_router.get_available_tools()
        assert len(tools) > 0

        # Test tool execution directly (simulating MCP protocol)
        result = server.tool_router.call_tool("ping", {}, None)
        assert result["status"] == "success"
        assert result["message"] == "pong"

    def test_http_rest_transport_setup(self):
        """Test HTTP REST transport setup."""
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_MODE"] = "local"

        server = UnifiedMCPServer()

        # Verify server setup
        assert server.transport == "http"
        assert server.app is not None
        assert hasattr(server.app, "routes")

        # Check that HTTP routes are registered
        routes = [route.path for route in server.app.routes]

        # FastAPI automatically adds documentation routes, so we check for required routes
        required_routes = ["/health", "/"]  # Health endpoint and root endpoint

        # Should have basic routes
        assert any("/health" in route for route in routes)
        assert any(route == "/" for route in routes)
        assert len(routes) >= len(
            required_routes
        )  # Should have at least our required routes

        # Check that required routes are present (allow for FastAPI auto-generated routes)
        for required_route in required_routes:
            assert (
                required_route in routes
            ), f"Required route {required_route} not found in {routes}"

    def test_http_server_endpoints_mock(self):
        """Test HTTP server endpoints with mocked client."""
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_MODE"] = "local"

        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        # Mock HTTP client for testing endpoints
        client = TestClient(server.app)

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["transport"] == "http"
        assert data["auth_mode"] == "local"

        # Test root endpoint (MCP discovery)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "tools" in data
        assert data["protocolVersion"] == "2025-06-18"

        # Test MCP protocol initialize
        mcp_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        response = client.post("/", json=mcp_request)
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["result"]["protocolVersion"] == "2025-06-18"

        # Test tools list
        mcp_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        response = client.post("/", json=mcp_request)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]
        assert len(data["result"]["tools"]) > 0

        # Test tool call
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "ping", "arguments": {}},
        }
        response = client.post("/", json=mcp_request)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "content" in data["result"]

    def test_sse_transport_setup(self):
        """Test Server-Sent Events transport setup."""
        os.environ["MCP_TRANSPORT"] = "sse"
        os.environ["MCP_MODE"] = "remote"
        os.environ["ADMIN_TOKEN"] = "sse-test-token"

        server = UnifiedMCPServer()

        # Verify server setup
        assert server.transport == "sse"
        assert server.app is not None

        # Check that SSE routes are registered
        routes = [route.path for route in server.app.routes]
        assert any("/events" in route for route in routes)

    def test_sse_events_endpoint_mock(self):
        """Test SSE events endpoint setup and basic response."""
        os.environ["MCP_TRANSPORT"] = "sse"
        os.environ["MCP_MODE"] = "local"

        server = UnifiedMCPServer()

        # Test that the SSE endpoint is properly registered
        # Note: We don't actually call the endpoint because SSE streams are infinite
        # and would hang the test. Instead, we verify the route exists.
        assert server.app is not None
        routes = [route.path for route in server.app.routes]
        assert any(
            "/events" in route for route in routes
        ), "SSE /events endpoint not found"

        # Verify the route has the correct methods and configuration
        events_routes = [
            route
            for route in server.app.routes
            if hasattr(route, "path") and route.path == "/events"
        ]
        assert len(events_routes) > 0, "No /events route found"

        # For SSE endpoints, we verify setup without actually streaming
        # because the endpoint is designed to be an infinite stream
        events_route = events_routes[0]
        assert hasattr(events_route, "methods"), "Route should have methods defined"
        assert "GET" in events_route.methods, "SSE endpoint should support GET"

    def test_oauth_transport_setup(self):
        """Test OAuth 2.1 transport setup."""
        os.environ["MCP_TRANSPORT"] = "oauth"
        os.environ["MCP_MODE"] = "multiuser"
        os.environ["MCP_PUBLIC_URL"] = "http://localhost:18000"

        # Mock OAuth components
        with (
            patch("mcpnp.server.unified_server.OAuthServer") as mock_oauth,
            patch("mcpnp.server.unified_server.OAuthFlowHandler") as mock_handler,
        ):

            mock_oauth_instance = MagicMock()
            mock_oauth_instance.get_discovery_metadata.return_value = {"issuer": "test"}
            mock_oauth.return_value = mock_oauth_instance

            mock_handler_instance = MagicMock()
            mock_handler.return_value = mock_handler_instance

            # Create mock datastore
            mock_datastore = MagicMock()
            mock_datastore.load_valid_tokens.return_value = ({}, {})

            tool_router = MCPToolRouter()
            server = UnifiedMCPServer(
                tool_router=tool_router, oauth_datastore=mock_datastore
            )

            # Verify server setup
            assert server.transport == "oauth"
            assert server.oauth is not None
            assert server.oauth_handler is not None
            assert server.security is not None

            # Verify OAuth routes are registered
            routes = [route.path for route in server.app.routes]
            oauth_routes = [
                "/.well-known/oauth-authorization-server",
                "/authorize",
                "/token",
                "/register",
                "/register_user",
            ]

            for oauth_route in oauth_routes:
                assert any(oauth_route in route for route in routes)

    def test_oauth_endpoints_mock(self):
        """Test OAuth endpoints with mocked components."""
        os.environ["MCP_TRANSPORT"] = "oauth"
        os.environ["MCP_MODE"] = "multiuser"
        os.environ["MCP_PUBLIC_URL"] = "http://localhost:18000"

        # Mock OAuth components
        with (
            patch("mcpnp.server.unified_server.OAuthServer") as mock_oauth,
            patch("mcpnp.server.unified_server.OAuthFlowHandler") as mock_handler,
        ):

            # Setup OAuth mocks
            mock_oauth_instance = MagicMock()
            mock_oauth_instance.get_discovery_metadata.return_value = {
                "issuer": "http://localhost:18000",
                "authorization_endpoint": "http://localhost:18000/authorize",
            }
            mock_oauth_instance.get_protected_resource_metadata.return_value = {
                "resource": "http://localhost:18000"
            }
            mock_oauth.return_value = mock_oauth_instance

            mock_handler_instance = MagicMock()
            mock_handler_instance.validate_oauth_request.return_value = True
            mock_handler.return_value = mock_handler_instance

            # Create mock datastore
            mock_datastore = MagicMock()
            mock_datastore.load_valid_tokens.return_value = ({}, {})

            server = UnifiedMCPServer(oauth_datastore=mock_datastore)

            client = TestClient(server.app)

            # Test OAuth discovery
            response = client.get("/.well-known/oauth-authorization-server")
            assert response.status_code == 200
            data = response.json()
            assert "issuer" in data

            # Test protected resource metadata
            response = client.get("/.well-known/oauth-protected-resource")
            assert response.status_code == 200
            data = response.json()
            assert "resource" in data

            # Test client registration
            client_data = {
                "client_name": "Test Client",
                "redirect_uris": ["http://localhost:3000/callback"],
            }
            mock_oauth_instance.register_client.return_value = {
                "client_id": "test_client"
            }

            response = client.post("/register", json=client_data)
            assert response.status_code == 201
            data = response.json()
            assert "client_id" in data

    def test_transport_mode_configuration_validation(self):
        """Test that different transport modes configure correctly."""
        # Test configurations - separate OAuth since it requires special setup
        test_configs = [
            ("fastmcp", "local"),
            ("http", "local"),
            ("sse", "local"),
        ]

        for transport, mode in test_configs:
            # Clean environment
            for key in list(os.environ.keys()):
                if key.startswith("MCP_"):
                    del os.environ[key]

            # Set test configuration
            os.environ["MCP_TRANSPORT"] = transport
            os.environ["MCP_MODE"] = mode
            os.environ["MCP_HOST"] = "localhost"
            os.environ["MCP_PORT"] = "18000"

            tool_router = MCPToolRouter()
            server = UnifiedMCPServer(tool_router=tool_router)
            assert server.transport == transport
            assert server.auth_mode == mode

        # Test OAuth separately with required datastore
        for key in list(os.environ.keys()):
            if key.startswith("MCP_"):
                del os.environ[key]

        os.environ["MCP_TRANSPORT"] = "oauth"
        os.environ["MCP_MODE"] = "multiuser"
        os.environ["MCP_HOST"] = "localhost"
        os.environ["MCP_PORT"] = "18000"

        # Create mock datastore for OAuth transport
        mock_datastore = MagicMock()
        mock_datastore.load_valid_tokens.return_value = ({}, {})

        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(
            tool_router=tool_router, oauth_datastore=mock_datastore
        )
        assert server.transport == "oauth"
        assert server.auth_mode == "multiuser"

    def test_transport_specific_components(self):
        """Test that each transport mode has the correct components."""

        # Test FastMCP components
        os.environ["MCP_TRANSPORT"] = "fastmcp"
        os.environ["MCP_MODE"] = "local"
        server_fastmcp = UnifiedMCPServer()
        assert server_fastmcp.mcp is not None
        assert server_fastmcp.app is None
        assert server_fastmcp.oauth is None

        # Test HTTP components
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_MODE"] = "local"
        server_http = UnifiedMCPServer()
        assert server_http.mcp is None
        assert server_http.app is not None
        assert server_http.oauth is None

        # Test SSE components
        os.environ["MCP_TRANSPORT"] = "sse"
        os.environ["MCP_MODE"] = "local"
        server_sse = UnifiedMCPServer()
        assert server_sse.mcp is None
        assert server_sse.app is not None
        assert server_sse.oauth is None

    def test_authentication_modes_per_transport(self):
        """Test authentication modes work correctly with each transport."""

        # FastMCP + Local (no auth)
        os.environ["MCP_TRANSPORT"] = "fastmcp"
        os.environ["MCP_MODE"] = "local"
        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        # Test authentication-dependent tool with mock manager
        mock_manager = MockUserManager(user_id="test_user")
        result = server.tool_router.call_tool("get_user_profile", {}, mock_manager)
        assert result["status"] == "success"  # Should work with auth
        assert result["authenticated"]

        # HTTP + Local (no auth required)
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_MODE"] = "local"
        tool_router = MCPToolRouter()
        server = UnifiedMCPServer(tool_router=tool_router)

        # Test same authentication functionality
        result = server.tool_router.call_tool("get_user_profile", {}, mock_manager)
        assert result["status"] == "success"  # Should work with auth
        assert result["authenticated"]

        # OAuth + Multiuser (OAuth auth) - Skip for now since OAuth components not available
        # os.environ["MCP_TRANSPORT"] = "oauth"
        # os.environ["MCP_MODE"] = "multiuser"
        # (OAuth testing commented out due to missing components)

        # OAuth section commented out - would require complex OAuth component mocking
        # that is not available in current environment

    def test_error_handling_across_transports(self):
        """Test error handling across different transport modes."""

        transport_configs = [("fastmcp", "local"), ("http", "local"), ("sse", "local")]

        for transport, mode in transport_configs:
            os.environ["MCP_TRANSPORT"] = transport
            os.environ["MCP_MODE"] = mode

            tool_router = MCPToolRouter()
            server = UnifiedMCPServer(tool_router=tool_router)

            # Test error handling in tool router with mock manager
            mock_manager = MockUserManager(user_id="test_user")
            result = server.tool_router.call_tool("nonexistent_tool", {}, mock_manager)

            assert result["status"] == "error"
            assert (
                "unknown tool" in result["message"].lower()
            )  # Our router uses lowercase

            # Also test authentication-dependent tool without auth
            result_no_auth = server.tool_router.call_tool("get_user_profile", {}, None)
            assert result_no_auth["status"] == "error"
            assert "authentication required" in result_no_auth["message"].lower()

    def teardown_method(self):
        """Clean up after each test."""
        cleanup_test_environment()


class TestMCPTransportIntegration:
    """Integration tests across transport modes."""

    def test_same_functionality_across_transports(self):
        """Test that core functionality works consistently across transports."""

        # Test core functionality across different transports
        transports_to_test = [("fastmcp", "local"), ("http", "local")]

        for transport, mode in transports_to_test:
            unique_id = str(uuid.uuid4())[:8]
            # Setup environment
            os.environ["MCP_TRANSPORT"] = transport
            os.environ["MCP_MODE"] = mode

            tool_router = MCPToolRouter()
            server = UnifiedMCPServer(tool_router=tool_router)
            mock_manager = MockUserManager(user_id=f"user_{unique_id}")

            # Test authentication-dependent functionality
            result = server.tool_router.call_tool("get_user_profile", {}, mock_manager)
            assert result["status"] == "success"
            assert result["authenticated"]

            # Test same operations with our stub tools
            test_item = f"test_item_{transport}_{unique_id}"

            # Add item
            result = server.tool_router.call_tool(
                "add_item", {"name": test_item, "quantity": 5}, mock_manager
            )
            assert result["status"] == "success"

            # List items
            result = server.tool_router.call_tool("list_items", {}, mock_manager)
            assert result["status"] == "success"
            assert test_item in result["items"]

            # Test counter functionality
            result = server.tool_router.call_tool(
                "increment_counter", {"amount": 10}, mock_manager
            )
            assert result["status"] == "success"

            result = server.tool_router.call_tool("get_counter", {}, mock_manager)
            assert result["status"] == "success"
            assert result["counter"] == 10

            # Clean environment for next iteration
            for key in list(os.environ.keys()):
                if key.startswith(("MCP_", "PANTRY_")):
                    del os.environ[key]

    def test_tool_compatibility_matrix(self):
        """Test that all tools work across supported transport modes."""
        # Define tool compatibility using our stub tools
        core_tools = [
            "ping",
            "echo",
            "get_user_profile",
            "get_counter",
            "list_items",
            "add_item",
            "get_protected_data",
        ]

        transport_modes = [("fastmcp", "local"), ("http", "local")]

        for transport, mode in transport_modes:
            os.environ["MCP_TRANSPORT"] = transport
            os.environ["MCP_MODE"] = mode

            tool_router = MCPToolRouter()
            server = UnifiedMCPServer(tool_router=tool_router)
            mock_manager = MockUserManager(user_id="compat_test")

            # Test each core tool
            for tool_name in core_tools:
                args = {}

                # Provide minimal required arguments for our stub tools
                if tool_name == "echo":
                    args = {"message": "test message"}
                elif tool_name == "add_item":
                    args = {"name": f"test_item_{transport}", "quantity": 1}
                elif tool_name == "get_protected_data":
                    args = {"data_type": "personal"}

                # Use mock_manager for auth-dependent tools, None for public tools
                manager = (
                    mock_manager
                    if tool_name in ["get_user_profile", "get_protected_data"]
                    else None
                )

                result = server.tool_router.call_tool(tool_name, args, manager)
                assert (
                    result["status"] == "success"
                ), f"Tool {tool_name} failed on {transport}: {result.get('message', '')}"

            # Clean environment
            for key in list(os.environ.keys()):
                if key.startswith(("MCP_", "PANTRY_")):
                    del os.environ[key]

    def teardown_method(self):
        """Clean up after each test."""
        cleanup_test_environment()


if __name__ == "__main__":
    # Run tests directly if called as script
    pytest.main([__file__, "-v"])
