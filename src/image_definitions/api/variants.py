from typing import Dict, List, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models import Architecture, Variant
from ..schemas import Variant as VariantSchema
from ..schemas import VariantCreate, VariantUpdate

router = APIRouter()


@router.get("/", response_model=List[VariantSchema])
async def list_variants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    architecture_id: Optional[int] = Query(None, description="Filter by architecture ID"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[Variant]:
    """List all variants, optionally filtered by architecture."""
    query = select(Variant).offset(skip).limit(limit).order_by(Variant.created_at.desc())

    if architecture_id:
        query = query.where(Variant.architecture_id == architecture_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{variant_id}", response_model=VariantSchema)
async def get_variant(variant_id: int, db: AsyncSession = Depends(get_db)) -> Variant:
    """Get a specific variant by ID."""
    result = await db.execute(select(Variant).where(Variant.id == variant_id))
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    return variant


@router.post("/", response_model=VariantSchema, status_code=201)
async def create_variant(variant: VariantCreate, db: AsyncSession = Depends(get_db)) -> Variant:
    """Create a new variant."""
    # Verify architecture exists
    result = await db.execute(select(Architecture).where(Architecture.id == variant.architecture_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Architecture not found")

    db_variant = Variant(**variant.model_dump())
    db.add(db_variant)
    await db.commit()
    await db.refresh(db_variant)

    return db_variant


@router.patch("/{variant_id}", response_model=VariantSchema)
async def update_variant(variant_id: int, variant_update: VariantUpdate, db: AsyncSession = Depends(get_db)) -> Variant:
    """Update an existing variant."""
    result = await db.execute(select(Variant).where(Variant.id == variant_id))
    db_variant = result.scalar_one_or_none()

    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    update_data = variant_update.model_dump(exclude_unset=True)

    # Verify architecture exists if being updated
    if "architecture_id" in update_data:
        result = await db.execute(select(Architecture).where(Architecture.id == update_data["architecture_id"]))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Architecture not found")

    for field, value in update_data.items():
        setattr(db_variant, field, value)

    await db.commit()
    await db.refresh(db_variant)

    return db_variant


@router.delete("/{variant_id}")
async def delete_variant(variant_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Delete a variant and all its artifacts."""
    result = await db.execute(select(Variant).where(Variant.id == variant_id))
    db_variant = result.scalar_one_or_none()

    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    await db.delete(db_variant)
    await db.commit()

    return {"message": "Variant deleted successfully"}
