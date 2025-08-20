from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from ..models.artifact import ArtifactStatus, ArtifactType


class ArtifactBase(BaseModel):
    """Base schema for Artifact."""

    name: str
    artifact_type: ArtifactType
    location: Optional[str] = None
    region: Optional[str] = None
    account_id: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    build_id: Optional[str] = None
    build_metadata: Optional[Dict[str, Any]] = None


class ArtifactCreate(ArtifactBase):
    """Schema for creating an Artifact."""

    variant_id: int
    status: ArtifactStatus = ArtifactStatus.PENDING


class ArtifactUpdate(BaseModel):
    """Schema for updating an Artifact."""

    name: Optional[str] = None
    artifact_type: Optional[ArtifactType] = None
    status: Optional[ArtifactStatus] = None
    location: Optional[str] = None
    region: Optional[str] = None
    account_id: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    build_id: Optional[str] = None
    build_metadata: Optional[Dict[str, Any]] = None
    variant_id: Optional[int] = None


class Artifact(ArtifactBase):
    """Schema for Artifact responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ArtifactStatus
    variant_id: int
    created_at: datetime
    updated_at: datetime
