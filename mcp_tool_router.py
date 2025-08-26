"""MCP Tool Router - Stub implementation for testing"""

import logging
import traceback
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class MockUserManager:
    """Mock user manager for testing authentication-dependent tools."""

    def __init__(self, user_id: str = "test_user", authenticated: bool = True):
        self.user_id = user_id
        self.authenticated = authenticated


def log_tool_error(error: Exception, tool_name: str, context: str = ""):
    """Log tool error with full traceback."""
    try:
        tb_str = traceback.format_exc()
        error_msg = f"""Error in tool '{tool_name}' {context}: {error!s}

Full traceback:
{tb_str}"""
        logger.error(error_msg)
    except Exception:
        logger.exception("Failed to log tool error")
        logger.exception("Original error in %s: %s", tool_name, error)


class MCPToolRouter:
    """Routes MCP tool calls to appropriate test implementations."""

    def __init__(self):
        self.tools: dict[str, Callable] = {}
        self.test_data = {
            "users": {"test_user": {"name": "Test User", "email": "test@example.com"}},
            "items": {"apple": 10, "banana": 5, "orange": 3},
            "counter": 0,
        }
        self._register_tools()

    def _register_tools(self):
        """Register all test tools."""
        self.tools = {
            "ping": self._ping,
            "echo": self._echo,
            "get_counter": self._get_counter,
            "increment_counter": self._increment_counter,
            "reset_counter": self._reset_counter,
            "add_item": self._add_item,
            "remove_item": self._remove_item,
            "list_items": self._list_items,
            "get_user": self._get_user,
            "update_user": self._update_user,
            "simulate_error": self._simulate_error,
            "validate_params": self._validate_params,
            "get_user_profile": self._get_user_profile,
            "get_protected_data": self._get_protected_data,
            "admin_status": self._admin_status,
        }

    def call_tool(
        self, tool_name: str, arguments: dict[str, Any], manager=None
    ) -> dict[str, Any]:
        """Route tool call to appropriate test implementation."""
        if tool_name not in self.tools:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        try:
            return self.tools[tool_name](arguments, manager)
        except Exception as e:
            log_tool_error(e, tool_name, "during execution")
            return {"status": "error", "message": f"Tool execution failed: {e!s}"}

    def get_available_tools(self) -> list:
        """Get list of available test tools."""
        return [
            {
                "name": "ping",
                "description": "Simple ping test that returns pong",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
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
                "name": "get_counter",
                "description": "Get the current counter value",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "increment_counter",
                "description": "Increment the counter by a specified amount",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "integer",
                            "description": "Amount to increment",
                            "default": 1,
                        }
                    },
                },
            },
            {
                "name": "reset_counter",
                "description": "Reset the counter to zero",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "add_item",
                "description": "Add an item with quantity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Item name"},
                        "quantity": {
                            "type": "integer",
                            "description": "Item quantity",
                            "default": 1,
                        },
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "remove_item",
                "description": "Remove quantity from an item",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Item name"},
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to remove",
                            "default": 1,
                        },
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "list_items",
                "description": "List all items and their quantities",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_user",
                "description": "Get user information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Username"}
                    },
                    "required": ["username"],
                },
            },
            {
                "name": "update_user",
                "description": "Update user information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Username"},
                        "name": {"type": "string", "description": "Full name"},
                        "email": {"type": "string", "description": "Email address"},
                    },
                    "required": ["username"],
                },
            },
            {
                "name": "simulate_error",
                "description": "Simulate an error for testing error handling",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "error_type": {
                            "type": "string",
                            "description": "Type of error to simulate",
                            "enum": ["ValueError", "RuntimeError", "KeyError"],
                            "default": "RuntimeError",
                        }
                    },
                },
            },
            {
                "name": "validate_params",
                "description": "Test parameter validation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "required_param": {
                            "type": "string",
                            "description": "Required parameter",
                        },
                        "optional_param": {
                            "type": "string",
                            "description": "Optional parameter",
                        },
                        "number_param": {
                            "type": "number",
                            "description": "Number parameter",
                        },
                    },
                    "required": ["required_param"],
                },
            },
            {
                "name": "get_user_profile",
                "description": "Get authenticated user profile (requires authentication)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_protected_data",
                "description": "Get protected data specific to the authenticated user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data_type": {
                            "type": "string",
                            "description": "Type of protected data to retrieve",
                            "enum": ["personal", "settings", "history"],
                            "default": "personal",
                        }
                    },
                },
            },
            {
                "name": "admin_status",
                "description": "Check admin status of the authenticated user",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    # Tool implementations
    def _ping(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Simple ping test."""
        return {
            "status": "success",
            "message": "pong",
            "timestamp": "2024-01-01T00:00:00Z",
        }

    def _echo(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Echo back the provided message."""
        message = arguments.get("message", "")
        return {"status": "success", "echo": message, "length": len(message)}

    def _get_counter(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Get current counter value."""
        return {"status": "success", "counter": self.test_data["counter"]}

    def _increment_counter(
        self, arguments: dict[str, Any], manager=None
    ) -> dict[str, Any]:
        """Increment counter by specified amount."""
        amount = arguments.get("amount", 1)
        self.test_data["counter"] += amount
        return {
            "status": "success",
            "message": f"Counter incremented by {amount}",
            "counter": self.test_data["counter"],
        }

    def _reset_counter(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Reset counter to zero."""
        old_value = self.test_data["counter"]
        self.test_data["counter"] = 0
        return {
            "status": "success",
            "message": f"Counter reset from {old_value} to 0",
            "counter": 0,
        }

    def _add_item(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Add item with quantity."""
        name = arguments.get("name")
        quantity = arguments.get("quantity", 1)

        if not name:
            return {"status": "error", "message": "Item name is required"}

        if name in self.test_data["items"]:
            self.test_data["items"][name] += quantity
            action = "updated"
        else:
            self.test_data["items"][name] = quantity
            action = "added"

        return {
            "status": "success",
            "message": f"Item '{name}' {action}",
            "name": name,
            "quantity": self.test_data["items"][name],
        }

    def _remove_item(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Remove quantity from item."""
        name = arguments.get("name")
        quantity = arguments.get("quantity", 1)

        if not name:
            return {"status": "error", "message": "Item name is required"}

        if name not in self.test_data["items"]:
            return {"status": "error", "message": f"Item '{name}' not found"}

        current_qty = self.test_data["items"][name]
        if current_qty < quantity:
            return {
                "status": "error",
                "message": f"Cannot remove {quantity}, only {current_qty} available",
            }

        self.test_data["items"][name] -= quantity
        if self.test_data["items"][name] == 0:
            del self.test_data["items"][name]

        return {
            "status": "success",
            "message": f"Removed {quantity} of '{name}'",
            "remaining": self.test_data["items"].get(name, 0),
        }

    def _list_items(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """List all items and quantities."""
        return {
            "status": "success",
            "items": dict(self.test_data["items"]),
            "total_items": len(self.test_data["items"]),
        }

    def _get_user(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Get user information."""
        username = arguments.get("username")

        if not username:
            return {"status": "error", "message": "Username is required"}

        if username not in self.test_data["users"]:
            return {"status": "error", "message": f"User '{username}' not found"}

        return {
            "status": "success",
            "user": dict(self.test_data["users"][username]),
            "username": username,
        }

    def _update_user(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Update user information."""
        username = arguments.get("username")
        name = arguments.get("name")
        email = arguments.get("email")

        if not username:
            return {"status": "error", "message": "Username is required"}

        if username not in self.test_data["users"]:
            self.test_data["users"][username] = {}

        user = self.test_data["users"][username]
        updates = []

        if name is not None:
            user["name"] = name
            updates.append("name")

        if email is not None:
            user["email"] = email
            updates.append("email")

        return {
            "status": "success",
            "message": f"Updated user '{username}': {', '.join(updates)}",
            "user": dict(user),
        }

    def _simulate_error(
        self, arguments: dict[str, Any], manager=None
    ) -> dict[str, Any]:
        """Simulate an error for testing."""
        error_type = arguments.get("error_type", "RuntimeError")

        if error_type == "ValueError":
            raise ValueError("Simulated ValueError for testing")
        if error_type == "KeyError":
            raise KeyError("Simulated KeyError for testing")
        raise RuntimeError("Simulated RuntimeError for testing")

    def _validate_params(
        self, arguments: dict[str, Any], manager=None
    ) -> dict[str, Any]:
        """Test parameter validation."""
        required_param = arguments.get("required_param")
        optional_param = arguments.get("optional_param")
        number_param = arguments.get("number_param")

        if not required_param:
            return {"status": "error", "message": "required_param is required"}

        result = {
            "status": "success",
            "message": "Parameters validated successfully",
            "received_params": {
                "required_param": required_param,
                "optional_param": optional_param,
                "number_param": number_param,
            },
        }

        return result

    def _get_user_profile(
        self, arguments: dict[str, Any], manager=None
    ) -> dict[str, Any]:
        """Get authenticated user profile (simulates authentication requirement)."""
        if manager is None:
            return {
                "status": "error",
                "message": "Authentication required - no user session",
            }

        # Simulate different user profiles based on manager type/id
        user_id = getattr(manager, "user_id", "test_user")

        # Mock user profiles
        profiles = {
            "test_user": {
                "user_id": "test_user",
                "username": "testuser",
                "email": "test@example.com",
                "role": "user",
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T10:30:00Z",
            },
            "admin_user": {
                "user_id": "admin_user",
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "created_at": "2023-01-01T00:00:00Z",
                "last_login": "2024-01-15T11:00:00Z",
            },
        }

        profile = profiles.get(str(user_id), profiles["test_user"])

        return {"status": "success", "profile": profile, "authenticated": True}

    def _get_protected_data(
        self, arguments: dict[str, Any], manager=None
    ) -> dict[str, Any]:
        """Get protected data specific to authenticated user."""
        if manager is None:
            return {
                "status": "error",
                "message": "Authentication required - no user session",
            }

        data_type = arguments.get("data_type", "personal")
        user_id = getattr(manager, "user_id", "test_user")

        # Mock protected data
        protected_data = {
            "personal": {
                "preferences": {"theme": "dark", "language": "en"},
                "private_notes": ["Note 1", "Note 2"],
                "api_keys": ["key_***masked***"],
            },
            "settings": {
                "notifications": True,
                "privacy_level": "medium",
                "data_retention": "1year",
            },
            "history": {
                "last_actions": ["login", "view_profile", "update_settings"],
                "login_count": 42,
                "last_activity": "2024-01-15T10:30:00Z",
            },
        }

        return {
            "status": "success",
            "data_type": data_type,
            "user_id": str(user_id),
            "data": protected_data.get(data_type, {}),
            "authenticated": True,
        }

    def _admin_status(self, arguments: dict[str, Any], manager=None) -> dict[str, Any]:
        """Check admin status of authenticated user."""
        if manager is None:
            return {
                "status": "error",
                "message": "Authentication required - no user session",
            }

        user_id = getattr(manager, "user_id", "test_user")

        # Mock admin users
        admin_users = ["admin_user", "root", "administrator"]
        is_admin = str(user_id) in admin_users

        return {
            "status": "success",
            "user_id": str(user_id),
            "is_admin": is_admin,
            "admin_level": "full" if is_admin else "none",
            "permissions": ["read", "write", "delete"] if is_admin else ["read"],
            "authenticated": True,
        }
