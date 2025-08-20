from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductGroupBase(BaseModel):
    """Base schema for ProductGroup."""

    name: str
    description: Optional[str] = None


class ProductGroupCreate(ProductGroupBase):
    """Schema for creating a ProductGroup."""

    pass


class ProductGroupUpdate(BaseModel):
    """Schema for updating a ProductGroup."""

    name: Optional[str] = None
    description: Optional[str] = None


class ProductGroup(ProductGroupBase):
    """Schema for ProductGroup responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    # Include related products in responses if needed
    # products: List["Product"] = []
