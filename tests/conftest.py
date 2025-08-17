"""
Configuration for MCP core tests.
"""

import os
import sys
from pathlib import Path

# Add project root to path for all tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def cleanup_test_environment():
    """Clean up test environment variables."""
    env_vars_to_clean = [
        "MCP_TRANSPORT",
        "MCP_MODE",
        "MCP_HOST",
        "MCP_PORT",
        "MCP_PUBLIC_URL",
        "ADMIN_TOKEN",
    ]
    for var in env_vars_to_clean:
        os.environ.pop(var, None)
