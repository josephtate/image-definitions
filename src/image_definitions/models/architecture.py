from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .product import Product
    from .variant import Variant


class Architecture(Base):
    """An architecture configuration for a product (e.g., x86_64, aarch64)."""

    __tablename__ = "architectures"

    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # x86_64, aarch64, etc.
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Human-readable name
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign key
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="architectures")
    variants: Mapped[List["Variant"]] = relationship(
        "Variant", back_populates="architecture", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Architecture(id={self.id}, name='{self.name}', product_id={self.product_id})>"
