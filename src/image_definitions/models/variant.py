from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .architecture import Architecture
    from .artifact import Artifact


class Variant(Base):
    """A specific configuration variant of a product."""

    __tablename__ = "variants"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    build_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Build configuration parameters

    # Foreign key
    architecture_id: Mapped[int] = mapped_column(ForeignKey("architectures.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    architecture: Mapped["Architecture"] = relationship("Architecture", back_populates="variants")
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact", back_populates="variant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Variant(id={self.id}, name='{self.name}', architecture_id={self.architecture_id})>"
