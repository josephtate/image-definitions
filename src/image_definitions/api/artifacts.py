from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models import Artifact, Variant
from ..models.artifact import ArtifactStatus, ArtifactType
from ..schemas import Artifact as ArtifactSchema
from ..schemas import ArtifactCreate, ArtifactUpdate

router = APIRouter()


@router.get("/", response_model=List[ArtifactSchema])
async def list_artifacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    variant_id: int = Query(None, description="Filter by variant ID"),
    artifact_type: ArtifactType = Query(None, description="Filter by artifact type"),
    status: ArtifactStatus = Query(None, description="Filter by status"),
    region: str = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_db),
):
    """List all artifacts with optional filtering."""
    query = select(Artifact).offset(skip).limit(limit).order_by(Artifact.created_at.desc())

    if variant_id:
        query = query.where(Artifact.variant_id == variant_id)

    if artifact_type:
        query = query.where(Artifact.artifact_type == artifact_type)

    if status:
        query = query.where(Artifact.status == status)

    if region:
        query = query.where(Artifact.region == region)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{artifact_id}", response_model=ArtifactSchema)
async def get_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific artifact by ID."""
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifact


@router.post("/", response_model=ArtifactSchema, status_code=201)
async def create_artifact(artifact: ArtifactCreate, db: AsyncSession = Depends(get_db)):
    """Create a new artifact."""
    # Verify variant exists
    result = await db.execute(select(Variant).where(Variant.id == artifact.variant_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Variant not found")

    db_artifact = Artifact(**artifact.model_dump())
    db.add(db_artifact)
    await db.commit()
    await db.refresh(db_artifact)

    return db_artifact


@router.patch("/{artifact_id}", response_model=ArtifactSchema)
async def update_artifact(artifact_id: int, artifact_update: ArtifactUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing artifact."""
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    db_artifact = result.scalar_one_or_none()

    if not db_artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    update_data = artifact_update.model_dump(exclude_unset=True)

    # Verify variant exists if being updated
    if "variant_id" in update_data:
        result = await db.execute(select(Variant).where(Variant.id == update_data["variant_id"]))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Variant not found")

    for field, value in update_data.items():
        setattr(db_artifact, field, value)

    await db.commit()
    await db.refresh(db_artifact)

    return db_artifact


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an artifact."""
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    db_artifact = result.scalar_one_or_none()

    if not db_artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    await db.delete(db_artifact)
    await db.commit()

    return {"message": "Artifact deleted successfully"}


@router.get("/stats/summary")
async def get_artifact_stats(db: AsyncSession = Depends(get_db)):
    """Get summary statistics for artifacts."""
    # Count by type
    type_counts = await db.execute(
        select(Artifact.artifact_type, func.count().label("count")).group_by(Artifact.artifact_type)
    )

    # Count by status
    status_counts = await db.execute(select(Artifact.status, func.count().label("count")).group_by(Artifact.status))

    # Total size
    total_size_result = await db.execute(select(func.sum(Artifact.size_bytes).label("total_size")))
    total_size = total_size_result.scalar() or 0

    return {
        "by_type": {row.artifact_type: row.count for row in type_counts},
        "by_status": {row.status: row.count for row in status_counts},
        "total_size_bytes": total_size,
    }
