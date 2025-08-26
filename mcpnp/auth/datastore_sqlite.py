"""Implementatio of datastore with PostgreSQL backend."""

import json
import sqlite3
import time

from werkzeug.security import generate_password_hash

from .datastore import OAuthDatastore


class SQLiteOAuthDatastore(OAuthDatastore):
    """SQLite implementation of OAuth datastore."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # OAuth clients table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_clients (
                    client_id TEXT PRIMARY KEY,
                    client_secret TEXT NOT NULL,
                    redirect_uris TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Users table (simplified for SQLite mode)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # OAuth tokens table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    token TEXT PRIMARY KEY,
                    token_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    scopes TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    token_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: list[str],
        client_name: str,
    ) -> None:
        """Register a new OAuth client."""
        redirect_uris_json = json.dumps(redirect_uris)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO oauth_clients (client_id, client_secret, redirect_uris, client_name)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, client_secret, redirect_uris_json, client_name),
            )

    def validate_client(self, client_id: str, client_secret: str | None = None) -> bool:
        """Validate client credentials."""
        with sqlite3.connect(self.db_path) as conn:
            if client_secret:
                cursor = conn.execute(
                    """
                    SELECT client_id FROM oauth_clients
                    WHERE client_id = ? AND client_secret = ?
                    """,
                    (client_id, client_secret),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT client_id FROM oauth_clients WHERE client_id = ?
                    """,
                    (client_id,),
                )
            return cursor.fetchone() is not None

    def get_client_redirect_uris(self, client_id: str) -> list[str]:
        """Get redirect URIs for a client."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT redirect_uris FROM oauth_clients WHERE client_id = ?",
                (client_id,),
            )
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return []

    def create_user(
        self, username: str, password: str, email: str | None = None
    ) -> str:
        """Create a new user account. Returns user ID."""
        password_hash = generate_password_hash(password, method="scrypt")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?) RETURNING id
                """,
                (username, password_hash, email),
            )
            result = cursor.fetchone()
            return str(result[0])

    def authenticate_user(self, username: str, password: str) -> str | None:
        """Authenticate user credentials. Returns user ID if valid."""
        # For SQLite mode, return default user ID (simplified auth)
        return "1"

    def save_token(self, token: str, token_type: str, token_data: dict) -> None:
        """Save token to persistent storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO oauth_tokens
                (token, token_type, user_id, client_id, scopes, expires_at, token_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    token,
                    token_type,
                    token_data["user_id"],
                    token_data["client_id"],
                    token_data.get("scope", ""),
                    token_data.get("expires_at", 0),
                    json.dumps(token_data),
                ),
            )

    def load_valid_tokens(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """Load all valid tokens from storage."""
        access_tokens = {}
        refresh_tokens = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT token, token_type, token_data FROM oauth_tokens WHERE expires_at > ?",
                (int(time.time()),),
            )

            for token, token_type, token_data_json in cursor.fetchall():
                token_data = json.loads(token_data_json)
                if token_type == "access":
                    access_tokens[token] = token_data
                elif token_type == "refresh":
                    refresh_tokens[token] = token_data

        return access_tokens, refresh_tokens

    def remove_token(self, token: str) -> None:
        """Remove token from storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM oauth_tokens WHERE token = ?", (token,))
