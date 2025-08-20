#!/usr/bin/env python3
"""Command-line interface for Image Definitions."""

import sys
from typing import Any, Dict, Optional, Union

import configargparse
import httpx
from rich.console import Console
from rich.table import Table

from .core.config import parse_cli_args

console = Console()


class ImageDefinitionsClient:
    """CLI client for Image Definitions API."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        # Get settings for default values
        cli_settings = parse_cli_args()
        self.base_url = base_url or f"http://{cli_settings.host}:{cli_settings.port}"
        self.client = httpx.Client(base_url=f"{self.base_url}/api", timeout=timeout)

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Make HTTP request with error handling."""
        try:
            response = self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            console.print(f"[red]HTTP error: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    # Product Groups
    def list_product_groups(self) -> None:
        """List all product groups."""
        groups = self._request("GET", "/product-groups")

        if not groups:
            console.print("No product groups found.")
            return

        table = Table(title="Product Groups")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Description")
        table.add_column("Created", style="dim")

        for group in groups:
            table.add_row(
                str(group["id"]),
                group["name"],
                group["description"] or "No description",
                group["created_at"][:10],  # Just the date part
            )

        console.print(table)

    def create_product_group(self, name: str, description: Optional[str] = None) -> None:
        """Create a new product group."""
        data = {"name": name}
        if description:
            data["description"] = description

        result = self._request("POST", "/product-groups", json=data)
        console.print(f"[green]Created product group '{result['name']}'[/green]")

    def delete_product_group(self, group_id: int) -> None:
        """Delete a product group."""
        self._request("DELETE", f"/product-groups/{group_id}")
        console.print(f"[green]Deleted product group {group_id}[/green]")

    # Products
    def list_products(self, product_group_id: Optional[int] = None) -> None:
        """List all products, optionally filtered by product group."""
        params = {}
        if product_group_id:
            params["product_group_id"] = product_group_id

        products = self._request("GET", "/products", params=params)

        if not products:
            console.print("No products found.")
            return

        table = Table(title="Products")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Group ID", style="blue")
        table.add_column("Created", style="dim")

        for product in products:
            table.add_row(
                str(product["id"]),
                product["name"],
                product["version"] or "No version",
                str(product["product_group_id"]),
                product["created_at"][:10],
            )

        console.print(table)

    def create_product(
        self, name: str, product_group_id: int, version: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        """Create a new product."""
        data = {"name": name, "product_group_id": product_group_id}
        if version:
            data["version"] = version
        if description:
            data["description"] = description

        result = self._request("POST", "/products", json=data)
        console.print(f"[green]Created product '{result['name']}'[/green]")

    # Variants
    def list_variants(self, product_id: Optional[int] = None) -> None:
        """List all variants, optionally filtered by product."""
        params = {}
        if product_id:
            params["product_id"] = product_id

        variants = self._request("GET", "/variants", params=params)

        if not variants:
            console.print("No variants found.")
            return

        table = Table(title="Variants")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Architecture", style="yellow")
        table.add_column("Product ID", style="blue")
        table.add_column("Created", style="dim")

        for variant in variants:
            table.add_row(
                str(variant["id"]),
                variant["name"],
                variant["architecture"] or "Any",
                str(variant["product_id"]),
                variant["created_at"][:10],
            )

        console.print(table)

    # Artifacts
    def list_artifacts(
        self, variant_id: Optional[int] = None, artifact_type: Optional[str] = None, status: Optional[str] = None
    ) -> None:
        """List all artifacts with optional filtering."""
        params: Dict[str, Union[int, str]] = {}
        if variant_id is not None:
            params["variant_id"] = variant_id
        if artifact_type:
            params["artifact_type"] = artifact_type
        if status:
            params["status"] = status

        artifacts = self._request("GET", "/artifacts", params=params)

        if not artifacts:
            console.print("No artifacts found.")
            return

        table = Table(title="Artifacts")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Region")
        table.add_column("Created", style="dim")

        for artifact in artifacts:
            # Color status based on value
            status_color = {
                "completed": "green",
                "building": "blue",
                "pending": "yellow",
                "failed": "red",
                "deprecated": "dim",
            }.get(artifact["status"], "white")

            table.add_row(
                str(artifact["id"]),
                artifact["name"],
                artifact["artifact_type"].replace("_", " ").title(),
                f"[{status_color}]{artifact['status']}[/{status_color}]",
                artifact["region"] or "N/A",
                artifact["created_at"][:10],
            )

        console.print(table)

    def get_artifact_stats(self) -> None:
        """Show artifact statistics."""
        stats = self._request("GET", "/artifacts/stats/summary")

        console.print("\n[bold]Artifact Statistics[/bold]")

        # By status
        console.print("\n[yellow]By Status:[/yellow]")
        for status, count in stats["by_status"].items():
            color = {
                "completed": "green",
                "building": "blue",
                "pending": "yellow",
                "failed": "red",
                "deprecated": "dim",
            }.get(status, "white")
            console.print(f"  [{color}]{status.title()}: {count}[/{color}]")

        # By type
        console.print("\n[yellow]By Type:[/yellow]")
        for artifact_type, count in stats["by_type"].items():
            console.print(f"  {artifact_type.replace('_', ' ').title()}: {count}")

        # Total size
        total_bytes = stats["total_size_bytes"]
        if total_bytes:
            # Convert to human readable
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if total_bytes < 1024.0:
                    console.print(f"\n[yellow]Total Size:[/yellow] {total_bytes:.1f} {unit}")
                    break
                total_bytes /= 1024.0
        else:
            console.print("\n[yellow]Total Size:[/yellow] 0 B")


def main() -> None:
    """Main CLI entry point."""
    parser = configargparse.ArgParser(description="Image Definitions CLI", default_config_files=[".env"])

    parser.add_argument("--base-url", env_var="API_BASE_URL", help="Base URL for the API server")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Product Groups commands
    pg_parser = subparsers.add_parser("groups", help="Product group operations")
    pg_subparsers = pg_parser.add_subparsers(dest="groups_action")

    pg_subparsers.add_parser("list", help="List product groups")

    pg_create = pg_subparsers.add_parser("create", help="Create product group")
    pg_create.add_argument("--name", required=True, help="Product group name")
    pg_create.add_argument("--description", help="Product group description")

    pg_delete = pg_subparsers.add_parser("delete", help="Delete product group")
    pg_delete.add_argument("--id", type=int, required=True, help="Product group ID")

    # Products commands
    p_parser = subparsers.add_parser("products", help="Product operations")
    p_subparsers = p_parser.add_subparsers(dest="products_action")

    p_list = p_subparsers.add_parser("list", help="List products")
    p_list.add_argument("--group-id", type=int, help="Filter by product group ID")

    p_create = p_subparsers.add_parser("create", help="Create product")
    p_create.add_argument("--name", required=True, help="Product name")
    p_create.add_argument("--group-id", type=int, required=True, help="Product group ID")
    p_create.add_argument("--version", help="Product version")
    p_create.add_argument("--description", help="Product description")

    # Variants commands
    v_parser = subparsers.add_parser("variants", help="Variant operations")
    v_subparsers = v_parser.add_subparsers(dest="variants_action")

    v_list = v_subparsers.add_parser("list", help="List variants")
    v_list.add_argument("--product-id", type=int, help="Filter by product ID")

    # Artifacts commands
    a_parser = subparsers.add_parser("artifacts", help="Artifact operations")
    a_subparsers = a_parser.add_subparsers(dest="artifacts_action")

    a_list = a_subparsers.add_parser("list", help="List artifacts")
    a_list.add_argument("--variant-id", type=int, help="Filter by variant ID")
    a_list.add_argument("--type", help="Filter by artifact type")
    a_list.add_argument("--status", help="Filter by status")

    a_subparsers.add_parser("stats", help="Show artifact statistics")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create client
    client = ImageDefinitionsClient(args.base_url)

    try:
        # Route to appropriate handler
        if args.command == "groups":
            if args.groups_action == "list":
                client.list_product_groups()
            elif args.groups_action == "create":
                client.create_product_group(args.name, args.description)
            elif args.groups_action == "delete":
                client.delete_product_group(args.id)
            else:
                pg_parser.print_help()

        elif args.command == "products":
            if args.products_action == "list":
                client.list_products(args.group_id)
            elif args.products_action == "create":
                client.create_product(args.name, args.group_id, args.version, args.description)
            else:
                p_parser.print_help()

        elif args.command == "variants":
            if args.variants_action == "list":
                client.list_variants(args.product_id)
            else:
                v_parser.print_help()

        elif args.command == "artifacts":
            if args.artifacts_action == "list":
                client.list_artifacts(args.variant_id, getattr(args, "type"), args.status)
            elif args.artifacts_action == "stats":
                client.get_artifact_stats()
            else:
                a_parser.print_help()

        else:
            parser.print_help()

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
