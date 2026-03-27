from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import SearchResponse
from app.services.search import search_service
from app.config import settings

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=2, max_length=500, description="Search query"),
    k: int = Query(default=settings.search_top_k_default, ge=1, le=50, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await search_service.semantic_search(query=q, k=k, db=db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}")
