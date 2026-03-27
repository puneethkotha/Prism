from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Product, ProductTag
from app.schemas import ProductResponse, ExtractedTags

router = APIRouter(prefix="/product", tags=["products"])


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await db.execute(
        select(ProductTag).where(ProductTag.product_id == product_id)
    )
    pt = result.scalar_one_or_none()
    tags = None
    if pt:
        try:
            tags = ExtractedTags(**pt.tags)
        except Exception:
            pass

    return ProductResponse(
        id=product.id,
        asin=product.asin,
        title=product.title,
        description=product.description,
        raw_text=product.raw_text,
        tags=tags,
        created_at=product.created_at,
    )
