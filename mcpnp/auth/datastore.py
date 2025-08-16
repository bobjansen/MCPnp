"""
Database abstraction layer for OAuth server.
Provides consistent interface for SQLite and PostgreSQL backends.
"""

import json
import sqlite3
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor


class OAuthDatastore(ABC):
    """Abstract base class for OAuth data storage."""

    @abstractmethod
    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str],
        client_name: str,
    ) -> None:
        """Register a new OAuth client."""
        pass

    @abstractmethod
    def validate_client(self, client_id: str, client_secret: str = None) -> bool:
        """Validate client credentials."""
        pass

    @abstractmethod
    def get_client_redirect_uris(self, client_id: str) -> List[str]:
        """Get redirect URIs for a client."""
        pass

    @abstractmethod
    def create_user(self, username: str, password_hash: str, email: str = None) -> str:
        """Create a new user account. Returns user ID."""
        pass

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user credentials. Returns user ID if valid."""
        pass

    @abstractmethod
    def save_token(self, token: str, token_type: str, token_data: Dict) -> None:
        """Save token to persistent storage."""
        pass

    @abstractmethod
    def load_valid_tokens(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """Load all valid tokens from storage. Returns (access_tokens, refresh_tokens)."""
        pass

    @abstractmethod
    def remove_token(self, token: str) -> None:
        """Remove token from storage."""
        pass

    @abstractmethod
    def init_database(self) -> None:
        """Initialize database schema."""
        pass


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
        redirect_uris: List[str],
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

    def validate_client(self, client_id: str, client_secret: str = None) -> bool:
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

    def get_client_redirect_uris(self, client_id: str) -> List[str]:
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

    def create_user(self, username: str, password_hash: str, email: str = None) -> str:
        """Create a new user account. Returns user ID."""
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

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user credentials. Returns user ID if valid."""
        # For SQLite mode, return default user ID (simplified auth)
        return "1"

    def save_token(self, token: str, token_type: str, token_data: Dict) -> None:
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

    def load_valid_tokens(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
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


class PostgreSQLOAuthDatastore(OAuthDatastore):
    """PostgreSQL implementation of OAuth datastore."""

    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.init_database()

    def init_database(self) -> None:
        """Initialize PostgreSQL database schema."""
        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor() as cursor:
                # OAuth clients table
                cursor.execute(
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

                # Users table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # OAuth tokens table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS oauth_tokens (
                        token TEXT PRIMARY KEY,
                        token_type TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        client_id TEXT NOT NULL,
                        scopes TEXT NOT NULL,
                        expires_at BIGINT NOT NULL,
                        token_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                conn.commit()

    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str],
        client_name: str,
    ) -> None:
        """Register a new OAuth client."""
        redirect_uris_json = json.dumps(redirect_uris)
        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO oauth_clients (client_id, client_secret, redirect_uris, client_name)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (client_id, client_secret, redirect_uris_json, client_name),
                )
                conn.commit()

    def validate_client(self, client_id: str, client_secret: str = None) -> bool:
        """Validate client credentials."""
        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor() as cursor:
                if client_secret:
                    cursor.execute(
                        """
                        SELECT client_id FROM oauth_clients
                        WHERE client_id = %s AND client_secret = %s
                        """,
                        (client_id, client_secret),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT client_id FROM oauth_clients WHERE client_id = %s
                        """,
                        (client_id,),
                    )
                return cursor.fetchone() is not None

    def get_client_redirect_uris(self, client_id: str) -> List[str]:
        """Get redirect URIs for a client."""
        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT redirect_uris FROM oauth_clients WHERE client_id = %s",
                    (client_id,),
                )
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return []

    def create_user(self, username: str, password_hash: str, email: str = None) -> str:
        """Create a new user account. Returns user ID."""
        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                try:
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, email)
                        VALUES (%s, %s, %s) RETURNING id
                        """,
                        (username, password_hash, email),
                    )
                    result = cursor.fetchone()
                    conn.commit()
                    return str(result["id"])
                except psycopg2.IntegrityError:
                    raise ValueError("Username already exists")

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user credentials. Returns user ID if valid."""
        from werkzeug.security import check_password_hash

        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, username, password_hash FROM users WHERE username = %s",
                    (username,),
                )

                user = cursor.fetchone()
                if not user:
                    return None

                # Verify password using werkzeug's check_password_hash
                if check_password_hash(user["password_hash"], password):
                    return str(user["id"])
                return None

    def save_token(self, token: str, token_type: str, token_data: Dict) -> None:
        """Save token to persistent storage."""
        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO oauth_tokens
                    (token, token_type, user_id, client_id, scopes, expires_at, token_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (token) DO UPDATE SET
                    token_data = EXCLUDED.token_data, expires_at = EXCLUDED.expires_at
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
                conn.commit()

    def load_valid_tokens(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """Load all valid tokens from storage."""
        access_tokens = {}
        refresh_tokens = {}

        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT token, token_type, token_data FROM oauth_tokens WHERE expires_at > %s",
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
        with psycopg2.connect(self.connection_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM oauth_tokens WHERE token = %s", (token,))
                conn.commit()
