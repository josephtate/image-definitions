"""Test configuration and fixtures."""

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from image_definitions.core.database import get_db
from image_definitions.main import app
from image_definitions.models import Base

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def sync_engine():
    """Create a synchronous test database engine."""
    engine = create_engine(TEST_SYNC_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
async def async_engine():
    """Create an asynchronous test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """Create a test database session."""
    async_session_maker = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Create a test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    # Clean up override
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_product_group(db_session):
    """Create a sample product group for testing."""
    from image_definitions.models import ProductGroup

    product_group = ProductGroup(name="Test Group", description="A test product group")
    db_session.add(product_group)
    await db_session.commit()
    await db_session.refresh(product_group)

    return product_group


@pytest.fixture
async def sample_product(db_session, sample_product_group):
    """Create a sample product for testing."""
    from image_definitions.models import Product

    product = Product(
        name="Test Product", description="A test product", version="1.0.0", product_group_id=sample_product_group.id
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    return product


@pytest.fixture
async def sample_architecture(db_session, sample_product):
    """Create a sample architecture for testing."""
    from image_definitions.models import Architecture

    architecture = Architecture(
        name="x86_64", display_name="x86_64", description="64-bit x86 architecture", product_id=sample_product.id
    )
    db_session.add(architecture)
    await db_session.commit()
    await db_session.refresh(architecture)

    return architecture


@pytest.fixture
async def sample_variant(db_session, sample_architecture):
    """Create a sample variant for testing."""
    from image_definitions.models import Variant

    variant = Variant(name="Test Variant", description="A test variant", architecture_id=sample_architecture.id)
    db_session.add(variant)
    await db_session.commit()
    await db_session.refresh(variant)

    return variant


@pytest.fixture
async def sample_artifact(db_session, sample_variant):
    """Create a sample artifact for testing."""
    from image_definitions.models import Artifact, ArtifactStatus, ArtifactType

    artifact = Artifact(
        name="Test Artifact",
        artifact_type=ArtifactType.BASE_IMAGE,
        status=ArtifactStatus.COMPLETED,
        location="s3://bucket/test-artifact.img",
        variant_id=sample_variant.id,
    )
    db_session.add(artifact)
    await db_session.commit()
    await db_session.refresh(artifact)

    return artifact
