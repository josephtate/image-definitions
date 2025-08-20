#!/usr/bin/env python3
"""Bootstrap script to load initial data from unified-config.yml."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from image_definitions.core.database import AsyncSessionLocal
from image_definitions.models import Architecture, Product, ProductGroup, Variant

console = Console()


class ConfigBootstrapper:
    """Bootstrap data from unified-config.yml into the database."""

    def __init__(
        self,
        config_file: Path = Path("unified-config.yml"),
        verbose: bool = False,
        blacklist: Optional[List[str]] = None,
    ):
        self.config_file = config_file
        self.verbose = verbose
        self.blacklist = [item.lower() for item in blacklist or ["CIQ-Kernel", "sig-cloud-next"]]
        self.config: Dict[str, Any] = {}
        self.stats = {
            "product_groups_created": 0,
            "products_created": 0,
            "variants_created": 0,
            "skipped": 0,
            "errors": 0,
        }

        # Configure logging based on verbose flag
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration based on verbose flag."""
        if not self.verbose:
            # Suppress SQLAlchemy INFO logging
            logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
            logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
        else:
            # Enable verbose logging
            logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    async def load_config(self) -> Dict[str, Any]:
        """Load and parse the YAML configuration file."""
        if not self.config_file.exists():
            console.print(f"[red]Configuration file not found: {self.config_file}[/red]")
            sys.exit(1)

        try:
            with open(self.config_file, "r") as f:
                self.config = yaml.safe_load(f)
            console.print(f"[green]Loaded configuration from {self.config_file}[/green]")
            return self.config
        except yaml.YAMLError as e:
            console.print(f"[red]Error parsing YAML file: {e}[/red]")
            sys.exit(1)

    async def show_preview(self) -> None:
        """Show a preview of what will be created."""
        if "product_groups" not in self.config:
            console.print("[yellow]No product_groups found in configuration[/yellow]")
            return

        table = Table(title="Preview: Data to be loaded")
        table.add_column("Product Group", style="cyan")
        table.add_column("Products", style="green")
        table.add_column("Architectures", style="yellow")
        table.add_column("Release Versions", style="magenta")

        product_groups = self.config["product_groups"]
        for group_name, group_data in product_groups.items():
            # Skip blacklisted groups in preview
            if group_name.lower() in self.blacklist:
                if self.verbose:
                    console.print(f"[yellow]Skipping blacklisted group in preview: {group_name}[/yellow]")
                continue

            if "products" not in group_data:
                continue

            products = list(group_data["products"].keys())
            arches_set = set()
            versions_set = set()

            for product_name, product_data in group_data["products"].items():
                if isinstance(product_data, dict):
                    if "arches" in product_data:
                        arches_set.update(product_data["arches"])
                    if "releasever" in product_data:
                        versions_set.add(str(product_data["releasever"]))

            table.add_row(
                group_name,
                ", ".join(products[:3]) + ("..." if len(products) > 3 else ""),
                ", ".join(sorted(arches_set)) if arches_set else "N/A",
                ", ".join(sorted(versions_set)) if versions_set else "N/A",
            )

        console.print(table)

    async def create_product_group(
        self, session: AsyncSession, name: str, description: Optional[str] = None
    ) -> Optional[ProductGroup]:
        """Create a product group if it doesn't exist."""
        try:
            # Check if exists
            result = await session.execute(select(ProductGroup).where(ProductGroup.name == name))
            existing = result.scalar_one_or_none()

            if existing:
                if self.verbose:
                    console.print(f"[yellow]Product group '{name}' already exists, skipping[/yellow]")
                self.stats["skipped"] += 1
                return existing

            # Create new product group
            pg = ProductGroup(name=name, description=description or f"Product group for {name} products")
            session.add(pg)
            await session.flush()  # Get the ID without committing
            if self.verbose:
                console.print(f"[green]Created product group: {name}[/green]")
            self.stats["product_groups_created"] += 1
            return pg

        except Exception as e:
            console.print(f"[red]Error creating product group '{name}': {e}[/red]")
            self.stats["errors"] += 1
            return None

    async def create_product(
        self,
        session: AsyncSession,
        name: str,
        product_group: ProductGroup,
        version: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Product]:
        """Create a product if it doesn't exist."""
        try:
            # Check if exists
            result = await session.execute(
                select(Product).where(Product.name == name, Product.product_group_id == product_group.id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                if self.verbose:
                    console.print(
                        f"[yellow]Product '{name}' already exists in group '{product_group.name}', skipping[/yellow]"
                    )
                self.stats["skipped"] += 1
                return existing

            # Create new product
            product = Product(
                name=name,
                version=version,
                description=description or f"Product {name}",
                product_group_id=product_group.id,
            )
            session.add(product)
            await session.flush()
            if self.verbose:
                console.print(f"[green]Created product: {name} (version: {version or 'N/A'})[/green]")
            self.stats["products_created"] += 1
            return product

        except Exception as e:
            console.print(f"[red]Error creating product '{name}': {e}[/red]")
            self.stats["errors"] += 1
            return None

    async def create_variants(
        self, session: AsyncSession, product: Product, arches: List[str], product_data: Dict[str, Any]
    ) -> List[Variant]:
        """Create variants for different architectures."""
        variants: List[Variant] = []

        for arch in arches:
            try:
                # First find or create Architecture
                result = await session.execute(
                    select(Architecture).where(Architecture.product_id == product.id, Architecture.name == arch)
                )
                architecture = result.scalar_one_or_none()

                if not architecture:
                    # Create new architecture
                    architecture = Architecture(
                        name=arch,
                        display_name=arch.replace("_", " ").title(),
                        description=f"{arch} architecture for {product.name}",
                        product_id=product.id,
                    )
                    session.add(architecture)
                    await session.flush()  # Get ID for the architecture

                # Check if variant exists for this architecture
                variant_result = await session.execute(
                    select(Variant).where(Variant.architecture_id == architecture.id)
                )
                existing_variant = variant_result.scalar_one_or_none()

                if existing_variant:
                    if self.verbose:
                        console.print(f"[yellow]Variant '{product.name}-{arch}' already exists, skipping[/yellow]")
                    self.stats["skipped"] += 1
                    variants.append(existing_variant)
                    continue

                # Create build config from YAML data
                build_config = {}
                if "releasever" in product_data:
                    build_config["releasever"] = product_data["releasever"]
                if "stages" in product_data:
                    build_config["stages"] = product_data["stages"]
                if "repository_groups" in product_data:
                    build_config["repository_groups"] = list(product_data["repository_groups"].keys())

                variant = Variant(
                    name=f"{product.name}-{arch}",
                    description=f"{product.name} for {arch} architecture",
                    build_config=build_config if build_config else None,
                    architecture_id=architecture.id,
                )
                session.add(variant)
                await session.flush()
                variants.append(variant)
                if self.verbose:
                    console.print(f"[green]Created variant: {variant.name}[/green]")
                self.stats["variants_created"] += 1

            except Exception as e:
                console.print(f"[red]Error creating variant for arch '{arch}': {e}[/red]")
                self.stats["errors"] += 1

        return variants

    async def process_product_groups(self, session: AsyncSession) -> None:
        """Process all product groups and products from the config."""
        if "product_groups" not in self.config:
            console.print("[yellow]No product_groups found in configuration[/yellow]")
            return

        product_groups_data = self.config["product_groups"]

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Processing configuration...", total=len(product_groups_data))

            for group_name, group_data in product_groups_data.items():
                progress.update(task, description=f"Processing group: {group_name}")

                # Skip blacklisted groups
                if group_name.lower() in self.blacklist:
                    if self.verbose:
                        console.print(f"[yellow]Skipping blacklisted group: {group_name}[/yellow]")
                    progress.advance(task)
                    continue

                # Create product group
                pg = await self.create_product_group(session, group_name)
                if not pg:
                    continue

                # Process products in this group
                if "products" not in group_data:
                    console.print(f"[yellow]No products found in group '{group_name}'[/yellow]")
                    progress.advance(task)
                    continue

                for product_name, product_data in group_data["products"].items():
                    # Handle "just_like" references by skipping for now
                    if isinstance(product_data, dict) and "just_like" in product_data:
                        if self.verbose:
                            console.print(f"[yellow]Skipping '{product_name}' - uses 'just_like' reference[/yellow]")
                        continue

                    if not isinstance(product_data, dict):
                        console.print(f"[yellow]Skipping '{product_name}' - invalid data format[/yellow]")
                        continue

                    # Create product
                    version = str(product_data.get("releasever", "1.0"))
                    product = await self.create_product(
                        session,
                        product_name,
                        pg,
                        version=version,
                        description=f"Product {product_name} version {version}",
                    )

                    if not product:
                        continue

                    # Create variants for different architectures
                    arches = product_data.get("arches", ["x86_64"])  # Default to x86_64
                    if arches:
                        await self.create_variants(session, product, arches, product_data)

                progress.advance(task)

    async def bootstrap(self, force: bool = False) -> None:
        """Main bootstrap method."""
        console.print("[bold blue]🚀 Image Definitions Bootstrap[/bold blue]")
        console.print()

        # Load configuration
        await self.load_config()

        # Show preview
        console.print("[bold]Preview of data to be loaded:[/bold]")
        await self.show_preview()
        console.print()

        # Confirm action unless forced
        if not force:
            if not Confirm.ask("Do you want to proceed with loading this data?"):
                console.print("[yellow]Bootstrap cancelled.[/yellow]")
                return

        # Initialize database
        console.print("[bold]Initializing database connection...[/bold]")

        async with AsyncSessionLocal() as session:
            try:
                # Process the data
                await self.process_product_groups(session)

                # Commit all changes
                await session.commit()
                console.print("[bold green]✅ All data committed successfully![/bold green]")

            except Exception as e:
                await session.rollback()
                console.print(f"[bold red]❌ Error during bootstrap: {e}[/bold red]")
                raise

        # Show summary
        self.show_summary()

    def show_summary(self) -> None:
        """Show a summary of what was created."""
        console.print()
        console.print("[bold]📊 Bootstrap Summary:[/bold]")

        table = Table()
        table.add_column("Item", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("Skipped", style="yellow")
        table.add_column("Errors", style="red")

        table.add_row(
            "Product Groups",
            str(self.stats["product_groups_created"]),
            str(self.stats["skipped"]),
            str(self.stats["errors"]),
        )
        table.add_row("Products", str(self.stats["products_created"]), "-", "-")
        table.add_row("Variants", str(self.stats["variants_created"]), "-", "-")

        console.print(table)
        console.print()

        total_created = (
            self.stats["product_groups_created"] + self.stats["products_created"] + self.stats["variants_created"]
        )

        if total_created > 0:
            console.print(f"[bold green]🎉 Successfully created {total_created} items![/bold green]")
            console.print("You can now view them in the web UI at http://localhost:8000")
        else:
            console.print("[yellow]No new items were created. Data may already exist.[/yellow]")


async def main() -> None:
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap Image Definitions database")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("unified-config.yml"),
        help="Path to configuration file (default: unified-config.yml)",
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--preview", action="store_true", help="Only show preview, don't load data")
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (shows all creation/skipping messages)"
    )
    parser.add_argument(
        "--blacklist",
        nargs="*",
        default=["CIQ-Kernel", "sig-cloud-next"],
        help="Product groups to skip (default: CIQ-Kernel sig-cloud-next)",
    )

    args = parser.parse_args()

    bootstrapper = ConfigBootstrapper(args.config, verbose=args.verbose, blacklist=args.blacklist)

    if args.preview:
        await bootstrapper.load_config()
        await bootstrapper.show_preview()
        return

    try:
        await bootstrapper.bootstrap(force=args.force)
    except KeyboardInterrupt:
        console.print("\n[yellow]Bootstrap interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Bootstrap failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
