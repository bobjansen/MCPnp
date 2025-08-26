"""Generic MCP Context management.

This module provides a generic context manager that can be configured with any
data manager factory and database setup function.
"""

import os
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from mcpnp.auth.user_manager import UserManager

LOCAL_DB_PATH = "user.sqlite"

# Context variable to store current user
current_user: ContextVar[str | None] = ContextVar("current_user", default=None)


class MCPContext:
    """Generic MCP server context for user authentication and resource management.

    This class can be configured with any data manager factory and database setup
    function to work with different types of applications.
    """

    def __init__(
        self,
        data_manager_factory: Callable | None = None,
        database_setup_func: Callable | None = None,
    ):
        """Initialize MCP context.

        Args:
            data_manager_factory: Function to create data manager instances
            database_setup_func: Function to setup/initialize databases
        """
        self.mode = os.getenv("MCP_MODE", "local")  # "local" or "multiuser"
        self.user_manager = UserManager(self.mode, database_setup_func)
        self.data_managers: dict[str, Any] = {}

        # Store the factory functions
        self.data_manager_factory = data_manager_factory
        self.database_setup_func = database_setup_func

        # Initialize local user in local mode
        if self.mode == "local" and self.data_manager_factory:
            local_user = "local_user"
            db_path = LOCAL_DB_PATH
            self.data_managers[local_user] = self.data_manager_factory(
                connection_string=db_path
            )

            if self.database_setup_func:
                self.database_setup_func(db_path)

    def authenticate_and_get_data_manager(self) -> tuple[str | None, Any | None]:
        """Authenticate user and return their data manager instance."""
        if self.mode == "local":
            user_id = "local_user"
            if user_id not in self.data_managers and self.data_manager_factory:
                db_path = LOCAL_DB_PATH
                self.data_managers[user_id] = self.data_manager_factory(
                    connection_string=db_path
                )
            return user_id, self.data_managers.get(user_id)

        # In multiuser mode, authentication is handled by OAuth
        # This method should not be used for multiuser mode
        return None, None

    def set_current_user(self, user_id: str):
        """Set the current user in context."""
        current_user.set(user_id)

    def get_current_user(self) -> str | None:
        """Get the current user from context."""
        return current_user.get()

    def get_data_manager(self, user_id: str) -> Any | None:
        """Get data manager for a specific user."""
        if user_id in self.data_managers:
            return self.data_managers[user_id]

        # Create data manager for new user if factory is available
        if self.data_manager_factory and self.mode == "multiuser":
            # In multiuser mode, each user gets their own database
            db_path = f"user_data/{user_id}/user.sqlite"

            # Ensure directory exists
            Path(db_path).parent.mkdir(exist_ok=True)

            # Create data manager instance
            data_manager = self.data_manager_factory(connection_string=db_path)
            self.data_managers[user_id] = data_manager

            # Initialize database if setup function provided
            if self.database_setup_func:
                self.database_setup_func(db_path)

            return data_manager

        return None

    def create_user(self, username: str) -> dict[str, Any]:
        """Create a new user."""
        if self.mode == "local":
            return {
                "status": "error",
                "message": "User creation not supported in local mode",
            }

        # In multiuser mode, delegate to user manager
        try:
            success = self.user_manager.create_user(username)
            if success:
                return {"status": "success", "message": f"User {username} created"}
        except Exception as e:
            return {"status": "error", "message": f"User creation failed: {e!s}"}
        return {"status": "error", "message": "User creation failed"}
