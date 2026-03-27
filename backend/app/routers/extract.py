from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Product, ProductTag
from app.schemas import ExtractRequest, ExtractResponse
from app.services.llm import llm_service
from app.services.embedding import embedding_service

router = APIRouter(prefix="/extract", tags=["extract"])


@router.post("", response_model=ExtractResponse)
async def extract_tags(request: ExtractRequest, db: AsyncSession = Depends(get_db)):
    try:
        tags, latency_ms = await llm_service.extract_tags(request.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM extraction failed: {exc}")

    if request.product_id is not None:
        product = await db.get(Product, request.product_id)
        if product:
            embed_text = embedding_service.text_for_embedding(product.title, tags.model_dump())
            vector = embedding_service.embed(embed_text)
            existing = await db.execute(
                select(ProductTag).where(ProductTag.product_id == request.product_id)
            )
            pt = existing.scalar_one_or_none()
            if pt:
                pt.tags = tags.model_dump()
                pt.embedding = vector
            else:
                pt = ProductTag(product_id=request.product_id, tags=tags.model_dump(), embedding=vector)
                db.add(pt)
            await db.commit()

    return ExtractResponse(tags=tags, product_id=request.product_id, latency_ms=round(latency_ms, 2))
