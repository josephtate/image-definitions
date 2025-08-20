# Image Definitions

A database and web UI for tracking Linux System Image builds, their variants, and final artifacts.

## Overview

This application manages a hierarchy of:
- **Product Groups** - High-level organizational units
- **Products** - Specific image products within groups
- **Variants** - Different configurations of products
- **Artifacts** - Generated build artifacts (base images, cloud images, region copies)

## Features

- RESTful API with automatic OpenAPI documentation
- Static HTML/JavaScript web UI with reporting
- Auto-generated CLI client
- SQLite database (PostgreSQL ready)
- Kubernetes deployment ready
- Future SAML authentication support

## Development Setup

### Prerequisites
- Python 3.9+
- Poetry
- direnv (optional but recommended)

### Quick Start

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Activate environment:**
   ```bash
   poetry shell
   # OR if using direnv:
   direnv allow
   ```

3. **Initialize database:**
   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the server:**
   ```bash
   poetry run uvicorn image_definitions.main:app --reload
   ```

5. **Access the application:**
   - Web UI: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - OpenAPI Spec: http://localhost:8000/openapi.json

### CLI Usage

```bash
# List all product groups
poetry run image-definitions groups list

# Create a new product
poetry run image-definitions products create --name "RHEL 9" --group-id 1

# Generate CLI client
poetry run python scripts/generate_client.py
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_api.py
```

## Deployment

### Docker
```bash
docker build -t image-definitions .
docker run -p 8000:8000 image-definitions
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

## API Structure

- `GET /api/product-groups` - List product groups
- `POST /api/product-groups` - Create product group
- `GET /api/products` - List products
- `POST /api/products` - Create product
- `GET /api/variants` - List variants
- `POST /api/variants` - Create variant
- `GET /api/artifacts` - List artifacts
- `POST /api/artifacts` - Create artifact

## Database Schema

The application uses a hierarchical structure:
```
ProductGroup (1) -> (N) Product (1) -> (N) Variant (1) -> (N) Artifact
```

Each level tracks metadata like creation time, build status, and configuration parameters.
