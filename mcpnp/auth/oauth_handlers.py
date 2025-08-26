"""OAuth flow handlers - Centralized OAuth logic to reduce duplication."""

import logging
import time
from urllib.parse import quote, urlencode

from fastapi import HTTPException
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)


class OAuthFlowHandler:
    """Handles OAuth flow operations with centralized logic."""

    def __init__(self, oauth_server):
        self.oauth = oauth_server

    def cleanup_existing_codes(self, client_id: str, user_id: str) -> None:
        """Remove any existing authorization codes for this client/user combination."""
        codes_to_remove = []
        for existing_code, existing_data in self.oauth.auth_codes.items():
            if (
                existing_data.get("client_id") == client_id
                and existing_data.get("user_id") == user_id
            ):
                codes_to_remove.append(existing_code)
                logger.info("Removing old authorization code: %s", existing_code)

        for old_code in codes_to_remove:
            del self.oauth.auth_codes[old_code]

    def create_auth_code_with_cleanup(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        scope: str,
        code_challenge: str,
        code_challenge_method: str,
    ) -> str:
        """Create authorization code after cleaning up existing ones."""
        self.cleanup_existing_codes(client_id, user_id)

        auth_code = self.oauth.create_authorization_code(
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )

        # Store debug info
        if auth_code in self.oauth.auth_codes:
            self.oauth.auth_codes[auth_code]["debug_timestamp"] = time.time()
            logger.info("Created authorization code: %s", auth_code)

        return auth_code

    def create_success_redirect(
        self, redirect_uri: str, auth_code: str, state: str | None = None
    ) -> RedirectResponse:
        """Create a successful OAuth redirect response."""
        params = {"code": auth_code}
        if state:
            params["state"] = state

        redirect_url = f"{redirect_uri}?{urlencode(params, safe='', quote_via=quote)}"

        logger.info("OAuth flow successful! Redirecting to: %s", redirect_url)
        logger.info("Authorization code: %s", auth_code)
        logger.info("State parameter: %s", state)

        return RedirectResponse(url=redirect_url, status_code=302)

    def create_error_redirect(
        self,
        redirect_uri: str,
        error: str,
        error_description: str,
        state: str | None = None,
    ) -> RedirectResponse:
        """Create an error OAuth redirect response."""
        error_params = {"error": error, "error_description": error_description}
        if state:
            error_params["state"] = state

        redirect_url = f"{redirect_uri}?{urlencode(error_params)}"
        logger.error("OAuth error redirect: %s", redirect_url)

        return RedirectResponse(url=redirect_url, status_code=302)

    def handle_claude_auto_registration(
        self, client_id: str, redirect_uri: str
    ) -> bool:
        """Handle auto-registration for Claude clients."""
        if not redirect_uri.startswith("https://claude.ai/api/"):
            return False

        logger.info("Auto-registering Claude client with ID: %s", client_id)

        redirect_uris = [redirect_uri, "https://claude.ai/api/mcp/auth_callback"]
        success = self.oauth.register_existing_client(
            client_id=client_id,
            client_name="Claude.ai (Auto-registered)",
            redirect_uris=redirect_uris,
        )

        if success:
            logger.info("Successfully auto-registered Claude client: %s", client_id)
        else:
            logger.error("Failed to auto-register Claude client: %s", client_id)

        return success

    def validate_oauth_request(
        self, client_id: str, redirect_uri: str, code_challenge: str | None = None
    ) -> None:
        """Validate OAuth authorization request parameters."""
        # Validate client
        if not self.oauth.validate_client(client_id):
            logger.error("Invalid client_id: %s", client_id)

            # Try auto-registration for Claude
            if not self.handle_claude_auto_registration(client_id, redirect_uri):
                raise HTTPException(status_code=400, detail="Invalid client_id")

        # Validate redirect URI
        if not self.oauth.validate_redirect_uri(client_id, redirect_uri):
            logger.error(
                "Invalid redirect_uri for client %s: %s", client_id, redirect_uri
            )
            raise HTTPException(status_code=400, detail="Invalid redirect_uri")

        # PKCE is required
        if not code_challenge:
            logger.error("Missing code_challenge for client %s", client_id)
            raise HTTPException(status_code=400, detail="code_challenge required")

    def authenticate_and_create_code(
        self,
        username: str,
        password: str,
        client_id: str,
        redirect_uri: str,
        scope: str,
        code_challenge: str,
        code_challenge_method: str,
    ) -> tuple[str, str]:
        """Authenticate user and create authorization code."""
        # Authenticate user
        user_id = self.oauth.authenticate_user(username, password)
        logger.info("Authentication result for %s: %s", username, user_id)

        if not user_id:
            logger.error("Authentication failed for username: %s", username)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create authorization code
        logger.info("Creating authorization code for user %s", user_id)
        auth_code = self.create_auth_code_with_cleanup(
            client_id,
            user_id,
            redirect_uri,
            scope,
            code_challenge,
            code_challenge_method,
        )

        return user_id, auth_code

    def register_and_create_code(
        self,
        username: str,
        password: str,
        email: str | None,
        client_id: str,
        redirect_uri: str,
        scope: str,
        code_challenge: str,
        code_challenge_method: str,
    ) -> tuple[str, str]:
        """Register new user and create authorization code."""
        # Create user
        user_id = self.oauth.create_user(username, password, email)
        logger.info("Created new user: %s", user_id)

        # Create authorization code
        auth_code = self.create_auth_code_with_cleanup(
            client_id,
            user_id,
            redirect_uri,
            scope,
            code_challenge,
            code_challenge_method,
        )

        return user_id, auth_code
