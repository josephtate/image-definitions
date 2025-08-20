from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models import ProductGroup
from ..schemas import ProductGroup as ProductGroupSchema
from ..schemas import ProductGroupCreate, ProductGroupUpdate

router = APIRouter()


@router.get("/", response_model=List[ProductGroupSchema])
async def list_product_groups(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
):
    """List all product groups."""
    result = await db.execute(select(ProductGroup).offset(skip).limit(limit).order_by(ProductGroup.created_at.desc()))
    return result.scalars().all()


@router.get("/{product_group_id}", response_model=ProductGroupSchema)
async def get_product_group(product_group_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific product group by ID."""
    result = await db.execute(select(ProductGroup).where(ProductGroup.id == product_group_id))
    product_group = result.scalar_one_or_none()

    if not product_group:
        raise HTTPException(status_code=404, detail="Product group not found")

    return product_group


@router.post("/", response_model=ProductGroupSchema, status_code=201)
async def create_product_group(product_group: ProductGroupCreate, db: AsyncSession = Depends(get_db)):
    """Create a new product group."""
    # Check if name already exists
    result = await db.execute(select(ProductGroup).where(ProductGroup.name == product_group.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Product group with name '{product_group.name}' already exists")

    db_product_group = ProductGroup(**product_group.model_dump())
    db.add(db_product_group)
    await db.commit()
    await db.refresh(db_product_group)

    return db_product_group


@router.patch("/{product_group_id}", response_model=ProductGroupSchema)
async def update_product_group(
    product_group_id: int, product_group_update: ProductGroupUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an existing product group."""
    result = await db.execute(select(ProductGroup).where(ProductGroup.id == product_group_id))
    db_product_group = result.scalar_one_or_none()

    if not db_product_group:
        raise HTTPException(status_code=404, detail="Product group not found")

    # Check for name conflicts if name is being updated
    update_data = product_group_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != db_product_group.name:
        result = await db.execute(select(ProductGroup).where(ProductGroup.name == update_data["name"]))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail=f"Product group with name '{update_data['name']}' already exists"
            )

    for field, value in update_data.items():
        setattr(db_product_group, field, value)

    await db.commit()
    await db.refresh(db_product_group)

    return db_product_group


@router.delete("/{product_group_id}")
async def delete_product_group(product_group_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a product group and all its products."""
    result = await db.execute(select(ProductGroup).where(ProductGroup.id == product_group_id))
    db_product_group = result.scalar_one_or_none()

    if not db_product_group:
        raise HTTPException(status_code=404, detail="Product group not found")

    await db.delete(db_product_group)
    await db.commit()

    return {"message": "Product group deleted successfully"}


@router.get("/{product_group_id}/products")
async def get_product_group_with_products(product_group_id: int, db: AsyncSession = Depends(get_db)):
    """Get a product group with all its products."""
    result = await db.execute(
        select(ProductGroup).options(selectinload(ProductGroup.products)).where(ProductGroup.id == product_group_id)
    )
    product_group = result.scalar_one_or_none()

    if not product_group:
        raise HTTPException(status_code=404, detail="Product group not found")

    return {
        "id": product_group.id,
        "name": product_group.name,
        "description": product_group.description,
        "created_at": product_group.created_at,
        "updated_at": product_group.updated_at,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in product_group.products
        ],
    }
