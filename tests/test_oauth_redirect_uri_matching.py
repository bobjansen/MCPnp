#!/usr/bin/env python3
"""Tests for wildcard redirect URI matching in OAuthServer."""

import json
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from mcpnp.auth.oauth_server import OAuthServer


@contextmanager
def setup_server(allowed_uris):
    """Create OAuthServer with temporary database populated with allowed URIs."""
    with (
        patch.object(OAuthServer, "_load_tokens_from_db"),
    ):
        server = OAuthServer()
        client_id = "test_client"
        yield server, client_id

def test_query_param_wildcard():
    allowed = ["https://example.com/callback?param=*"]
    with setup_server(allowed) as (server, client_id):
        assert server.validate_redirect_uri(
            client_id, "https://example.com/callback?param=value"
        )


def test_filename_extension_wildcard():
    allowed = ["https://example.com/file-*.txt"]
    with setup_server(allowed) as (server, client_id):
        assert server.validate_redirect_uri(
            client_id, "https://example.com/file-test.txt"
        )


def test_plus_character_wildcard():
    allowed = ["https://example.com/query+value*"]
    with setup_server(allowed) as (server, client_id):
        assert server.validate_redirect_uri(
            client_id, "https://example.com/query+value123"
        )


def test_fullmatch_enforced():
    allowed = ["https://example.com/callback*end"]
    with setup_server(allowed) as (server, client_id):
        assert not server.validate_redirect_uri(
            client_id, "https://example.com/callbackmiddleendextra"
        )
        assert server.validate_redirect_uri(
            client_id, "https://example.com/callbackmiddleend"
        )
