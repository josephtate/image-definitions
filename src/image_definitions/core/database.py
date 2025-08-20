from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Create sync engine for migrations and CLI
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

# Create async engine for FastAPI
async_database_url = settings.database_url
if async_database_url.startswith("sqlite"):
    async_database_url = async_database_url.replace("sqlite://", "sqlite+aiosqlite://")
elif async_database_url.startswith("postgresql"):
    async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in async_database_url else {},
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


def get_sync_db() -> Session:
    """Get synchronous database session for CLI and migrations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session for FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
