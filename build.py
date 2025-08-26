#!/usr/bin/env python3
"""
Build script for MCPnp package.

This script builds the package for distribution.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"🔨 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Build the package."""
    print("🚀 Building MCPnp package")

    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    if not (script_dir / "pyproject.toml").exists():
        print("❌ pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)

    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    for path in ["build", "dist", "*.egg-info"]:
        subprocess.run(f"rm -rf {path}", check=True, shell=True)

    # Run quality checks first
    if not run_command("uv run python check.py --quick", "Quality checks"):
        print("⚠️  Quality checks failed, but continuing with build...")

    # Build the package
    if not run_command("uv build", "Building package"):
        print("❌ Build failed")
        sys.exit(1)

    # List built files
    dist_dir = script_dir / "dist"
    if dist_dir.exists():
        print("\n📦 Built packages:")
        for file in dist_dir.glob("*"):
            print(f"  {file.name}")

    print("\n🎉 Build completed successfully!")
    print("\nTo install the built package:")
    print("  uv pip install dist/mcpnp-1.0.0-py3-none-any.whl")
    print("\nTo upload to PyPI:")
    print("  uv publish dist/*")


if __name__ == "__main__":
    main()
