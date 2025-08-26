"""MCP Core Templates."""

from .oauth_templates import (
    generate_error_page,
    generate_login_form,
    generate_register_form,
)

__all__ = ["generate_error_page", "generate_login_form", "generate_register_form"]
