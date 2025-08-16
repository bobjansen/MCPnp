"""
OAuth 2.1 Authorization Server for MCP
Implements OAuth 2.1 with PKCE for secure authentication
"""

import base64
import hashlib
import json
import logging
import os
import re
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode
from werkzeug.security import generate_password_hash

from .datastore import OAuthDatastore

logger = logging.getLogger(__name__)

SCOPES = ["read", "write", "admin"]


class OAuthServer:
    """OAuth 2.1 Authorization Server with PKCE support."""

    def __init__(
        self, datastore: OAuthDatastore, base_url: str = "http://localhost:8000"
    ):
        self.datastore = datastore
        self.base_url = base_url.rstrip("/")

        # OAuth endpoints
        self.authorization_endpoint = f"{self.base_url}/authorize"
        self.token_endpoint = f"{self.base_url}/token"
        self.registration_endpoint = f"{self.base_url}/register"

        # Cache for authorization codes and tokens (with database persistence)
        self.auth_codes: Dict[str, Dict] = {}
        self.access_tokens: Dict[str, Dict] = {}
        self.refresh_tokens: Dict[str, Dict] = {}

        # Load existing tokens from database on startup
        self._load_tokens_from_db()

    def get_discovery_metadata(self) -> Dict:
        """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
        return {
            "issuer": self.base_url,
            "authorization_endpoint": self.authorization_endpoint,
            "token_endpoint": self.token_endpoint,
            "registration_endpoint": self.registration_endpoint,
            "scopes_supported": SCOPES,
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": [
                "none"
            ],  # PKCE only, no client secrets
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "claims_supported": ["sub", "iss", "aud", "exp", "iat"],
            # Claude.ai specific metadata
            "registration_client_uri": f"{self.base_url}/register",
            "require_request_uri_registration": False,
            "require_signed_request_object": False,
        }

    def get_protected_resource_metadata(self) -> Dict:
        """OAuth 2.0 Protected Resource Metadata."""
        return {
            "resource": self.base_url,
            "authorization_servers": [self.base_url],
            "scopes_supported": SCOPES,
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{self.base_url}/docs",
        }

    def register_client(self, client_metadata: Dict) -> Dict:
        """Dynamic Client Registration (RFC 7591)."""
        client_id = secrets.token_urlsafe(16)
        client_secret = secrets.token_urlsafe(32)

        client_name = client_metadata.get("client_name", "Unnamed Client")
        redirect_uris = client_metadata.get("redirect_uris", [])

        logger.debug(
            "Registering client: %s, redirect_uris: %s", client_name, redirect_uris
        )
        logger.debug("Generated client_id: %s", client_id)

        # For Claude.ai, automatically add common proxy redirect patterns
        if "claude" in client_name.lower() or any(
            "claude.ai" in uri for uri in redirect_uris
        ):
            # Add wildcard pattern for Claude proxy URLs
            if not any("claude.ai/api/organizations" in uri for uri in redirect_uris):
                redirect_uris.append(
                    "https://claude.ai/api/organizations/*/mcp/oauth/callback"
                )
                logger.debug("Added Claude proxy redirect URI: %s", redirect_uris)

        # Use datastore to register client
        self.datastore.register_client(
            client_id, client_secret, redirect_uris, client_name
        )
        logger.debug("Client registered successfully")

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",  # Claude uses PKCE, no client secret needed
        }

    def create_user(self, username: str, password: str, email: str = None) -> str:
        """Create a new user account."""
        password_hash = generate_password_hash(password, method="scrypt")
        return self.datastore.create_user(username, password_hash, email)

    def register_user(self, username: str, email: str, password: str) -> bool:
        """Register a new user account. Returns True if successful."""
        try:
            self.create_user(username, password, email)
            return True
        except Exception:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user credentials."""
        return self.datastore.authenticate_user(username, password)

    def validate_client(self, client_id: str, client_secret: str = None) -> bool:
        """Validate client credentials."""
        logger.debug("Validating client_id: %s", client_id)
        result = self.datastore.validate_client(client_id, client_secret)
        logger.debug("Validation result: %s", result)
        return result

    def register_existing_client(
        self, client_id: str, client_name: str, redirect_uris: list
    ) -> bool:
        """Register a client with a specific client_id (for Claude Desktop compatibility)."""
        logger.debug("Registering existing client_id: %s", client_id)

        client_secret = secrets.token_urlsafe(32)

        try:
            self.datastore.register_client(
                client_id, client_secret, redirect_uris, client_name
            )
            logger.debug("Existing client registered successfully")
            return True
        except Exception as e:
            logger.error("Failed to register existing client: %s", e)
            return False

    def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """Validate redirect URI for client."""
        # Get allowed URIs from datastore
        allowed_uris = self.datastore.get_client_redirect_uris(client_id)
        if not allowed_uris:
            return False

        # Allow Claude.ai proxy redirects (flexible matching)
        if redirect_uri.startswith("https://claude.ai/api/organizations/") and (
            "mcp" in redirect_uri or "oauth" in redirect_uri
        ):
            return True

        # Exact match
        if redirect_uri in allowed_uris:
            return True

        # Wildcard matching for Claude patterns
        for allowed_uri in allowed_uris:
            if "*" in allowed_uri:
                # Build regex pattern using re.escape to handle special characters
                pattern = re.escape(allowed_uri).replace("\\*", ".*")
                if re.fullmatch(pattern, redirect_uri):
                    return True

        return False

    def verify_pkce_challenge(
        self, code_verifier: str, code_challenge: str, method: str = "S256"
    ) -> bool:
        """Verify PKCE code challenge."""
        if method == "S256":
            digest = hashlib.sha256(code_verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
            return challenge == code_challenge
        elif method == "plain":
            return code_verifier == code_challenge
        return False

    def create_authorization_code(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        scope: str,
        code_challenge: str,
        code_challenge_method: str,
    ) -> str:
        """Create authorization code."""
        code = secrets.token_urlsafe(32)
        expires_at = time.time() + 600  # 10 minutes

        self.auth_codes[code] = {
            "client_id": client_id,
            "user_id": user_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "expires_at": expires_at,
        }

        return code

    def exchange_code_for_tokens(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str,
        client_secret: str = None,
    ) -> Dict:
        """Exchange authorization code for access token."""
        if code not in self.auth_codes:
            raise ValueError("Invalid authorization code")

        auth_data = self.auth_codes[code]

        # Validate authorization code
        if time.time() > auth_data["expires_at"]:
            del self.auth_codes[code]
            raise ValueError("Authorization code expired")

        if auth_data["client_id"] != client_id:
            raise ValueError("Client ID mismatch")

        if auth_data["redirect_uri"] != redirect_uri:
            raise ValueError("Redirect URI mismatch")

        # Verify PKCE
        if not self.verify_pkce_challenge(
            code_verifier,
            auth_data["code_challenge"],
            auth_data["code_challenge_method"],
        ):
            raise ValueError("PKCE verification failed")

        # Generate tokens
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires_in = int(
            os.getenv("OAUTH_TOKEN_EXPIRY", "86400")
        )  # Default 24 hours, configurable

        # Store tokens in memory and database
        access_token_data = {
            "user_id": auth_data["user_id"],
            "client_id": client_id,
            "scope": auth_data["scope"],
            "expires_at": time.time() + expires_in,
        }

        refresh_token_data = {
            "user_id": auth_data["user_id"],
            "client_id": client_id,
            "scope": auth_data["scope"],
            "access_token": access_token,
            "expires_at": time.time()
            + (expires_in * 24),  # Refresh tokens last 24x longer than access tokens
        }

        self.access_tokens[access_token] = access_token_data
        self.refresh_tokens[refresh_token] = refresh_token_data

        # Persist tokens to database
        self.datastore.save_token(access_token, "access", access_token_data)
        self.datastore.save_token(refresh_token, "refresh", refresh_token_data)

        # Clean up authorization code
        del self.auth_codes[code]

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
            "scope": auth_data["scope"],
        }

    def validate_access_token(self, access_token: str) -> Optional[Dict]:
        """Validate access token and return token info."""
        if access_token not in self.access_tokens:
            return None

        token_data = self.access_tokens[access_token]

        if time.time() > token_data["expires_at"]:
            del self.access_tokens[access_token]
            self.datastore.remove_token(access_token)
            return None

        return token_data

    def refresh_access_token(self, refresh_token: str, client_id: str) -> Dict:
        """Refresh access token using refresh token."""
        if refresh_token not in self.refresh_tokens:
            raise ValueError("Invalid refresh token")

        refresh_data = self.refresh_tokens[refresh_token]

        # Check if refresh token is expired
        if "expires_at" in refresh_data and time.time() > refresh_data["expires_at"]:
            del self.refresh_tokens[refresh_token]
            self.datastore.remove_token(refresh_token)
            raise ValueError("Refresh token expired")

        if refresh_data["client_id"] != client_id:
            raise ValueError("Client ID mismatch")

        # Revoke old access token
        old_access_token = refresh_data["access_token"]
        if old_access_token in self.access_tokens:
            del self.access_tokens[old_access_token]

        # Generate new tokens
        new_access_token = secrets.token_urlsafe(32)
        new_refresh_token = secrets.token_urlsafe(32)
        expires_in = int(
            os.getenv("OAUTH_TOKEN_EXPIRY", "86400")
        )  # Default 24 hours, configurable

        # Store new tokens in memory and database
        new_access_token_data = {
            "user_id": refresh_data["user_id"],
            "client_id": client_id,
            "scope": refresh_data["scope"],
            "expires_at": time.time() + expires_in,
        }

        new_refresh_token_data = {
            "user_id": refresh_data["user_id"],
            "client_id": client_id,
            "scope": refresh_data["scope"],
            "access_token": new_access_token,
            "expires_at": time.time()
            + (expires_in * 24),  # Refresh tokens last 24x longer than access tokens
        }

        self.access_tokens[new_access_token] = new_access_token_data
        self.refresh_tokens[new_refresh_token] = new_refresh_token_data

        # Persist new tokens to database
        self.datastore.save_token(new_access_token, "access", new_access_token_data)
        self.datastore.save_token(new_refresh_token, "refresh", new_refresh_token_data)

        # Clean up old refresh token from memory and database
        del self.refresh_tokens[refresh_token]
        self.datastore.remove_token(refresh_token)

        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": new_refresh_token,
            "scope": refresh_data["scope"],
        }

    def _load_tokens_from_db(self):
        """Load existing tokens from database on startup."""
        try:
            access_tokens, refresh_tokens = self.datastore.load_valid_tokens()
            self.access_tokens.update(access_tokens)
            self.refresh_tokens.update(refresh_tokens)
        except Exception as e:
            logger.warning("Could not load tokens from database: %s", e)
