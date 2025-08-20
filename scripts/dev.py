#!/usr/bin/env python3
"""Development script for running the application locally."""

import os
import subprocess
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))


def run_migrations():
    """Run database migrations."""
    print("🔄 Running database migrations...")
    try:
        subprocess.run(["poetry", "run", "alembic", "upgrade", "head"], check=True)
        print("✅ Migrations completed successfully")
    except subprocess.CalledProcessError:
        print("❌ Migrations failed")
        return False
    return True


def create_initial_migration():
    """Create initial migration if migrations directory is empty."""
    versions_dir = Path("migrations/versions")
    if versions_dir.exists() and any(versions_dir.glob("*.py")):
        print("📁 Migrations already exist, skipping initial migration")
        return True

    print("🔄 Creating initial migration...")
    try:
        subprocess.run(
            ["poetry", "run", "alembic", "revision", "--autogenerate", "-m", "Initial migration"], check=True
        )
        print("✅ Initial migration created successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create initial migration")
        return False


def start_server():
    """Start the development server."""
    print("🚀 Starting development server...")
    try:
        subprocess.run(
            [
                "poetry",
                "run",
                "uvicorn",
                "image_definitions.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError:
        print("❌ Server failed to start")


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    try:
        subprocess.run(["poetry", "run", "pytest", "-v"], check=True)
        print("✅ All tests passed")
    except subprocess.CalledProcessError:
        print("❌ Some tests failed")
        return False
    return True


def run_linting():
    """Run code linting and formatting checks."""
    print("🔍 Running linting checks...")

    checks = [
        (["poetry", "run", "black", "--check", "."], "Black formatting"),
        (["poetry", "run", "isort", "--check-only", "."], "Import sorting"),
        (["poetry", "run", "flake8", "."], "Flake8 linting"),
        (["poetry", "run", "mypy", "src/image_definitions", "--ignore-missing-imports"], "Type checking"),
    ]

    all_passed = True
    for cmd, name in checks:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✅ {name}")
        except subprocess.CalledProcessError:
            print(f"  ❌ {name}")
            all_passed = False

    return all_passed


def fix_formatting():
    """Fix code formatting."""
    print("🔧 Fixing code formatting...")
    try:
        subprocess.run(["poetry", "run", "black", "."], check=True)
        subprocess.run(["poetry", "run", "isort", "."], check=True)
        print("✅ Code formatting fixed")
    except subprocess.CalledProcessError:
        print("❌ Failed to fix formatting")


def generate_openapi_spec():
    """Generate OpenAPI specification."""
    print("📋 Generating OpenAPI specification...")
    try:
        subprocess.run(["python", "scripts/generate_client.py"], check=True)
        print("✅ OpenAPI specification generated")
    except subprocess.CalledProcessError:
        print("❌ Failed to generate OpenAPI specification")


def run_bootstrap():
    """Run the bootstrap script to load initial data."""
    print("🚀 Running bootstrap to load initial data...")
    try:
        subprocess.run(["python", "scripts/bootstrap.py"], check=True)
        print("✅ Bootstrap completed successfully")
    except subprocess.CalledProcessError:
        print("❌ Bootstrap failed")
    except KeyboardInterrupt:
        print("\n👋 Bootstrap cancelled by user")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Image Definitions Development Script")
        print("")
        print("Usage: python scripts/dev.py <command>")
        print("")
        print("Commands:")
        print("  migrate        Run database migrations")
        print("  init-db        Create initial migration and run it")
        print("  bootstrap      Load initial data from unified-config.yml")
        print("  server         Start development server")
        print("  test           Run test suite")
        print("  lint           Run linting checks")
        print("  format         Fix code formatting")
        print("  openapi        Generate OpenAPI specification")
        print("  full-setup     Run init-db, then start server")
        return

    command = sys.argv[1]

    if command == "migrate":
        run_migrations()

    elif command == "init-db":
        if create_initial_migration():
            run_migrations()

    elif command == "server":
        start_server()

    elif command == "test":
        run_tests()

    elif command == "lint":
        if run_linting():
            print("✅ All linting checks passed")
        else:
            print("❌ Some linting checks failed")
            sys.exit(1)

    elif command == "format":
        fix_formatting()

    elif command == "bootstrap":
        run_bootstrap()

    elif command == "openapi":
        generate_openapi_spec()

    elif command == "full-setup":
        print("🏗️  Setting up development environment...")
        if create_initial_migration():
            if run_migrations():
                print("🎉 Setup complete! Starting server...")
                start_server()
            else:
                print("❌ Setup failed during migrations")
                sys.exit(1)
        else:
            print("❌ Setup failed during initial migration")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
