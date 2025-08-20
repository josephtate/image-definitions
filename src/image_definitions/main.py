import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import architectures, artifacts, product_groups, products, variants
from .core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Image Definitions API",
        description="Linux System Image Build Tracking Database and UI",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(product_groups.router, prefix=f"{settings.api_prefix}/product-groups", tags=["Product Groups"])
    app.include_router(products.router, prefix=f"{settings.api_prefix}/products", tags=["Products"])
    app.include_router(architectures.router, prefix=f"{settings.api_prefix}/architectures", tags=["Architectures"])
    app.include_router(variants.router, prefix=f"{settings.api_prefix}/variants", tags=["Variants"])
    app.include_router(artifacts.router, prefix=f"{settings.api_prefix}/artifacts", tags=["Artifacts"])

    # Mount static files
    # Go up from src/image_definitions/main.py -> src/image_definitions -> src -> project_root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    static_dir = os.path.join(project_root, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        """Serve the main HTML UI."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        static_dir = os.path.join(project_root, "static")
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Image Definitions API", "docs": "/docs"}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    return app


# Create the app instance
app = create_app()
