from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models import Architecture, Product
from ..schemas import Architecture as ArchitectureSchema
from ..schemas import ArchitectureCreate, ArchitectureUpdate

router = APIRouter()


@router.get("/", response_model=List[ArchitectureSchema])
async def list_architectures(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: int = Query(None, description="Filter by product ID"),
    db: AsyncSession = Depends(get_db),
):
    """List all architectures, optionally filtered by product."""
    query = select(Architecture).offset(skip).limit(limit).order_by(Architecture.created_at.desc())

    if product_id:
        query = query.where(Architecture.product_id == product_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{architecture_id}", response_model=ArchitectureSchema)
async def get_architecture(architecture_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific architecture by ID."""
    result = await db.execute(select(Architecture).where(Architecture.id == architecture_id))
    architecture = result.scalar_one_or_none()

    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    return architecture


@router.post("/", response_model=ArchitectureSchema, status_code=201)
async def create_architecture(architecture: ArchitectureCreate, db: AsyncSession = Depends(get_db)):
    """Create a new architecture."""
    # Verify product exists
    result = await db.execute(select(Product).where(Product.id == architecture.product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Product not found")

    db_architecture = Architecture(**architecture.model_dump())
    db.add(db_architecture)
    await db.commit()
    await db.refresh(db_architecture)

    return db_architecture


@router.patch("/{architecture_id}", response_model=ArchitectureSchema)
async def update_architecture(
    architecture_id: int, architecture_update: ArchitectureUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an existing architecture."""
    result = await db.execute(select(Architecture).where(Architecture.id == architecture_id))
    db_architecture = result.scalar_one_or_none()

    if not db_architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    update_data = architecture_update.model_dump(exclude_unset=True)

    # Verify product exists if being updated
    if "product_id" in update_data:
        result = await db.execute(select(Product).where(Product.id == update_data["product_id"]))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Product not found")

    for field, value in update_data.items():
        setattr(db_architecture, field, value)

    await db.commit()
    await db.refresh(db_architecture)

    return db_architecture


@router.delete("/{architecture_id}")
async def delete_architecture(architecture_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an architecture and all its variants."""
    result = await db.execute(select(Architecture).where(Architecture.id == architecture_id))
    db_architecture = result.scalar_one_or_none()

    if not db_architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")

    await db.delete(db_architecture)
    await db.commit()

    return {"message": "Architecture deleted successfully"}
