#!/usr/bin/env python3
"""Generate OpenAPI clients from the FastAPI application."""

import json
import os
import subprocess
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from image_definitions.main import app


def generate_openapi_spec():
    """Generate and save the OpenAPI specification."""
    spec = app.openapi()

    # Write to file
    spec_path = Path(__file__).parent.parent / "openapi.json"
    with open(spec_path, "w") as f:
        json.dump(spec, f, indent=2)

    print(f"OpenAPI specification written to: {spec_path}")
    return spec_path


def generate_python_client():
    """Generate Python client from OpenAPI spec using openapi-generator."""
    spec_path = generate_openapi_spec()
    client_dir = Path(__file__).parent.parent / "client" / "python"

    # Ensure output directory exists
    client_dir.mkdir(parents=True, exist_ok=True)

    # Check if openapi-generator is available
    try:
        subprocess.run(["openapi-generator-cli", "version"], check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("OpenAPI Generator CLI not found. Please install it:")
        print("npm install @openapitools/openapi-generator-cli -g")
        print("Or use Docker: docker run --rm openapitools/openapi-generator-cli version")
        return False

    # Generate client
    cmd = [
        "openapi-generator-cli",
        "generate",
        "-i",
        str(spec_path),
        "-g",
        "python",
        "-o",
        str(client_dir),
        "--package-name",
        "image_definitions_client",
        "--additional-properties",
        "packageVersion=0.1.0,projectName=image-definitions-client",
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Python client generated in: {client_dir}")

        # Create usage example
        example_path = client_dir / "example.py"
        with open(example_path, "w") as f:
            f.write(
                """#!/usr/bin/env python3
\"\"\"Example usage of the generated Python client.\"\"\"

import image_definitions_client
from image_definitions_client.rest import ApiException

# Configure the client
configuration = image_definitions_client.Configuration(
    host="http://localhost:8000/api"
)

# Create API client
with image_definitions_client.ApiClient(configuration) as api_client:
    # Create API instances
    product_groups_api = image_definitions_client.ProductGroupsApi(api_client)
    products_api = image_definitions_client.ProductsApi(api_client)

    try:
        # List product groups
        product_groups = product_groups_api.list_product_groups()
        print("Product Groups:", product_groups)

        # Create a new product group
        new_group = image_definitions_client.ProductGroupCreate(
            name="Example Group",
            description="Created via API client"
        )
        created_group = product_groups_api.create_product_group(new_group)
        print("Created group:", created_group)

    except ApiException as e:
        print("Exception when calling API: %s\\n" % e)
"""
            )

        print(f"Usage example created at: {example_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error generating Python client: {e}")
        return False


def generate_typescript_client():
    """Generate TypeScript client from OpenAPI spec."""
    spec_path = generate_openapi_spec()
    client_dir = Path(__file__).parent.parent / "client" / "typescript"

    # Ensure output directory exists
    client_dir.mkdir(parents=True, exist_ok=True)

    # Check if openapi-generator is available
    try:
        subprocess.run(["openapi-generator-cli", "version"], check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("OpenAPI Generator CLI not found. Skipping TypeScript client generation.")
        return False

    # Generate client
    cmd = [
        "openapi-generator-cli",
        "generate",
        "-i",
        str(spec_path),
        "-g",
        "typescript-fetch",
        "-o",
        str(client_dir),
        "--additional-properties",
        "npmName=image-definitions-client,npmVersion=0.1.0",
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"TypeScript client generated in: {client_dir}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error generating TypeScript client: {e}")
        return False


def main():
    """Main function."""
    print("Generating OpenAPI clients for Image Definitions API...")

    # Generate OpenAPI spec
    generate_openapi_spec()

    # Generate clients
    success = True

    if "--python" in sys.argv or "--all" in sys.argv or len(sys.argv) == 1:
        print("\\nGenerating Python client...")
        success &= generate_python_client()

    if "--typescript" in sys.argv or "--all" in sys.argv:
        print("\\nGenerating TypeScript client...")
        success &= generate_typescript_client()

    if success:
        print("\\n✅ Client generation completed successfully!")
        print("\\nTo use the generated clients:")
        print("1. Python: Install the generated package and import image_definitions_client")
        print("2. TypeScript: Run 'npm install' in the client/typescript directory")
    else:
        print("\\n❌ Some clients failed to generate. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Generate OpenAPI clients for Image Definitions API")
        print("\\nUsage: python generate_client.py [options]")
        print("\\nOptions:")
        print("  --python      Generate Python client only")
        print("  --typescript  Generate TypeScript client only")
        print("  --all         Generate all clients (default)")
        print("  --help, -h    Show this help message")
        sys.exit(0)

    main()
