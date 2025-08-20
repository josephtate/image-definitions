from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ArchitectureBase(BaseModel):
    """Base schema for Architecture."""

    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None


class ArchitectureCreate(ArchitectureBase):
    """Schema for creating an Architecture."""

    product_id: int


class ArchitectureUpdate(BaseModel):
    """Schema for updating an Architecture."""

    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    product_id: Optional[int] = None


class Architecture(ArchitectureBase):
    """Schema for Architecture responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime
