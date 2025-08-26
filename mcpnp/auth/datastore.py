"""Database abstraction layer for OAuth server.

Provides consistent interface for SQLite and PostgreSQL backends.
"""

from abc import ABC, abstractmethod


class OAuthDatastore(ABC):
    """Abstract base class for OAuth data storage."""

    @abstractmethod
    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: list[str],
        client_name: str,
    ) -> None:
        """Register a new OAuth client."""

    @abstractmethod
    def validate_client(self, client_id: str, client_secret: str | None = None) -> bool:
        """Validate client credentials."""

    @abstractmethod
    def get_client_redirect_uris(self, client_id: str) -> list[str]:
        """Get redirect URIs for a client."""

    @abstractmethod
    def create_user(
        self, username: str, password: str, email: str | None = None
    ) -> str:
        """Create a new user account. Returns user ID."""

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> str | None:
        """Authenticate user credentials. Returns user ID if valid."""

    @abstractmethod
    def save_token(self, token: str, token_type: str, token_data: dict) -> None:
        """Save token to persistent storage."""

    @abstractmethod
    def load_valid_tokens(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """Load all valid tokens from storage. Returns (access_tokens, refresh_tokens)."""

    @abstractmethod
    def remove_token(self, token: str) -> None:
        """Remove token from storage."""

    @abstractmethod
    def init_database(self) -> None:
        """Initialize database schema."""
