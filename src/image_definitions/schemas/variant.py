from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class VariantBase(BaseModel):
    """Base schema for Variant."""

    name: str
    description: Optional[str] = None
    build_config: Optional[Dict[str, Any]] = None


class VariantCreate(VariantBase):
    """Schema for creating a Variant."""

    architecture_id: int


class VariantUpdate(BaseModel):
    """Schema for updating a Variant."""

    name: Optional[str] = None
    description: Optional[str] = None
    build_config: Optional[Dict[str, Any]] = None
    architecture_id: Optional[int] = None


class Variant(VariantBase):
    """Schema for Variant responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    architecture_id: int
    created_at: datetime
    updated_at: datetime
