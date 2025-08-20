from typing import Dict, List, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models import Product, ProductGroup
from ..schemas import Product as ProductSchema
from ..schemas import ProductCreate, ProductUpdate

router = APIRouter()


@router.get("/", response_model=List[ProductSchema])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_group_id: Optional[int] = Query(None, description="Filter by product group ID"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[Product]:
    """List all products, optionally filtered by product group."""
    query = select(Product).offset(skip).limit(limit).order_by(Product.created_at.desc())

    if product_group_id:
        query = query.where(Product.product_group_id == product_group_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)) -> Product:
    """Get a specific product by ID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/", response_model=ProductSchema, status_code=201)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)) -> Product:
    """Create a new product."""
    # Verify product group exists
    result = await db.execute(select(ProductGroup).where(ProductGroup.id == product.product_group_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Product group not found")

    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.patch("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product_update: ProductUpdate, db: AsyncSession = Depends(get_db)) -> Product:
    """Update an existing product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)

    # Verify product group exists if being updated
    if "product_group_id" in update_data:
        result = await db.execute(select(ProductGroup).where(ProductGroup.id == update_data["product_group_id"]))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Product group not found")

    for field, value in update_data.items():
        setattr(db_product, field, value)

    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Delete a product and all its variants."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(db_product)
    await db.commit()

    return {"message": "Product deleted successfully"}
