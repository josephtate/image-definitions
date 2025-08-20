from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .product import Product


class ProductGroup(Base):
    """A high-level organizational unit for grouping related products."""

    __tablename__ = "product_groups"  # type: ignore[assignment]

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="product_group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProductGroup(id={self.id}, name='{self.name}')>"
