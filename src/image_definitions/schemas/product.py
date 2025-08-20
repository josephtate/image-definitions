from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    """Base schema for Product."""

    name: str
    description: Optional[str] = None
    version: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a Product."""

    product_group_id: int


class ProductUpdate(BaseModel):
    """Schema for updating a Product."""

    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    product_group_id: Optional[int] = None


class Product(ProductBase):
    """Schema for Product responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_group_id: int
    created_at: datetime
    updated_at: datetime
