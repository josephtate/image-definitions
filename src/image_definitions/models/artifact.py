from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, BigInteger
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .variant import Variant


class ArtifactType(str, Enum):
    """Types of artifacts that can be generated."""

    BASE_IMAGE = "base_image"
    CLOUD_IMAGE = "cloud_image"
    REGION_COPY = "region_copy"
    ACCOUNT_SHARE = "account_share"


class ArtifactStatus(str, Enum):
    """Status of artifact build/deployment."""

    PENDING = "pending"
    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class Artifact(Base):
    """A generated build artifact from a variant."""

    __tablename__ = "artifacts"  # type: ignore[assignment]

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(SQLEnum(ArtifactType), nullable=False, index=True)
    status: Mapped[ArtifactStatus] = mapped_column(
        SQLEnum(ArtifactStatus), nullable=False, default=ArtifactStatus.PENDING, index=True
    )

    # Location and metadata
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL, path, or identifier
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # AWS region, etc.
    account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # AWS account, etc.
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # SHA256, etc.

    # Build information
    build_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    build_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Foreign key
    variant_id: Mapped[int] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    variant: Mapped["Variant"] = relationship("Variant", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, name='{self.name}', type='{self.artifact_type}', status='{self.status}')>"
