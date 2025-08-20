from typing import Optional

import configargparse
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    database_url: str = "sqlite:///./image_definitions.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "info"

    # API
    api_prefix: str = "/api"

    # CORS
    cors_origins: list = ["*"]  # In production, specify actual origins

    # Future SAML settings
    saml_enabled: bool = False
    saml_metadata_url: Optional[str] = None

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


def get_settings() -> Settings:
    """Get settings from environment variables and .env file."""
    return Settings()


def parse_cli_args() -> Settings:
    """Parse command line arguments for CLI usage."""
    parser = configargparse.ArgParser(default_config_files=[".env"], description="Image Definitions CLI")

    parser.add_argument("--config", is_config_file=True, help="Config file path")
    parser.add_argument(
        "--database-url",
        env_var="DATABASE_URL",
        default="sqlite:///./image_definitions.db",
        help="Database connection URL",
    )
    parser.add_argument("--host", env_var="HOST", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", env_var="PORT", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", env_var="DEBUG", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--log-level",
        env_var="LOG_LEVEL",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level",
    )

    # Only parse known args to avoid conflicts with other tools
    args, _ = parser.parse_known_args()

    return Settings(
        database_url=args.database_url,
        host=args.host,
        port=args.port,
        debug=args.debug,
        log_level=args.log_level,
    )


# Global settings instance - use environment variables by default
settings = get_settings()
