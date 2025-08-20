from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .architecture import Architecture
    from .product_group import ProductGroup


class Product(Base):
    """A specific image product within a product group."""

    __tablename__ = "products"  # type: ignore[assignment]

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Foreign key
    product_group_id: Mapped[int] = mapped_column(ForeignKey("product_groups.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    product_group: Mapped["ProductGroup"] = relationship("ProductGroup", back_populates="products")
    architectures: Mapped[List["Architecture"]] = relationship(
        "Architecture", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', version='{self.version}')>"
