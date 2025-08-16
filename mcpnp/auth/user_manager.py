"""
Generic User Manager for MCP authentication.

Manages user authentication and database isolation for multi-user mode.
"""

import os
from typing import Callable, Optional


class UserManager:
    """
    Generic user authentication manager for multi-user MCP servers.

    Can be configured with different database setup functions to work with
    various types of applications.
    """

    def __init__(
        self, mode: str = "local", database_setup_func: Optional[Callable] = None
    ):
        """
        Initialize user manager.

        Args:
            mode: "local" or "multiuser" mode
            database_setup_func: Optional function to setup user databases
        """
        self.mode = mode  # "local" or "multiuser"
        self.database_setup_func = database_setup_func

    def authenticate(self, token: str) -> Optional[str]:
        """Authenticate a user by token and return user_id."""
        if self.mode == "local":
            return "local_user"

        # In multiuser mode, authentication is handled by OAuth
        # This method is not used for multiuser mode
        return None

    def create_user(self, username: str) -> str:
        """Create a new user and return their token."""
        if self.mode == "local":
            raise ValueError("Cannot create users in local mode")

        # In multiuser mode, user creation is handled by OAuth registration
        raise ValueError("User creation is handled by OAuth in multiuser mode")

    def list_users(self) -> list:
        """List all users (admin only)."""
        if self.mode == "local":
            return ["local_user"]

        # In multiuser mode, user listing is handled by OAuth/PostgreSQL
        return []
