# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Setup
```bash
# Install dependencies
poetry install

# Initialize database (create migrations and run them)
poetry run alembic upgrade head
# OR use the dev script for full setup
python scripts/dev.py init-db

# Load initial configuration data
python scripts/bootstrap.py
```

### Development Server
```bash
# Start development server with auto-reload
poetry run uvicorn image_definitions.main:app --reload

# OR use the dev script
python scripts/dev.py server
```

### Testing
```bash
# Run all tests with coverage
poetry run pytest

# Run specific test file
poetry run pytest tests/test_api.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality
```bash
# Run all linting checks
python scripts/dev.py lint

# Fix code formatting
python scripts/dev.py format

# Individual tools
poetry run black .              # Format code
poetry run isort .              # Sort imports
poetry run flake8 .             # Linting
poetry run mypy src/image_definitions --ignore-missing-imports  # Type checking
```

### Database Management
```bash
# Create new migration after model changes
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# View migration history
poetry run alembic history
```

### CLI Usage
```bash
# List product groups
poetry run image-definitions groups list

# Create new product
poetry run image-definitions products create --name "Product Name" --group-id 1

# Generate OpenAPI client
python scripts/generate_client.py
```

## Architecture Overview

This is a **FastAPI-based web application** for tracking Linux system image builds in a hierarchical structure:

### Data Model Hierarchy
```
ProductGroup → Product → Architecture → Variant → Artifact
```

- **Product Groups**: Top-level organizational units (e.g., "RLC", "FIPS", "LTS")
- **Products**: Specific image products within groups (e.g., "RLC-9", "FIPS-8_6")
- **Architectures**: CPU architectures for products (e.g., "x86_64", "aarch64")
- **Variants**: Different configurations within an architecture (e.g., build variants, feature sets)
- **Artifacts**: Generated build artifacts (base images, cloud images, region copies)

### Key Components

**API Structure** (`src/image_definitions/api/`):
- `product_groups.py` - CRUD operations for product groups
- `products.py` - Product management endpoints
- `architectures.py` - Architecture management endpoints
- `variants.py` - Variant management endpoints  
- `artifacts.py` - Artifact tracking endpoints

**Models** (`src/image_definitions/models/`):
- `base.py` - Base model with common fields (id, created_at, updated_at)
- Individual model files for each entity with SQLAlchemy definitions

**Configuration** (`src/image_definitions/core/`):
- `config.py` - Pydantic settings with environment variable support
- `database.py` - SQLAlchemy database configuration

**Application Entry** (`src/image_definitions/main.py`):
- FastAPI app factory with CORS, static file serving, and API routing

### Configuration Sources

The application uses a sophisticated configuration system:

1. **Environment Variables/CLI Args** - Runtime configuration (database URLs, server settings)
2. **unified-config.yml** - Complex hierarchical product/repository definitions loaded via bootstrap script
3. **Alembic** - Database schema migrations

### Database Support
- **Development**: SQLite (default: `image_definitions.db`)
- **Production**: PostgreSQL ready via `DATABASE_URL` environment variable
- **Migrations**: Alembic with automatic model detection

### Deployment
- **Docker**: Multi-stage build with production optimizations
- **Kubernetes**: Complete manifests in `k8s/` directory
- **Health Checks**: `/health` endpoint for monitoring

### Development Workflow
1. Use `scripts/dev.py` for common development tasks
2. Configuration loaded from `unified-config.yml` contains real production data structures
3. Static HTML/JS frontend served from `/static/` with API documentation at `/docs`
4. All models inherit from `Base` class providing automatic timestamps and table naming