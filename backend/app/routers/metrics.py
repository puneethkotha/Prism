import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import EvaluationMetrics, HealthResponse

router = APIRouter(tags=["metrics"])

METRICS_FILE = Path(__file__).parent.parent.parent / "data" / "evaluation_metrics.json"


@router.get("/metrics", response_model=EvaluationMetrics)
async def get_metrics(db: AsyncSession = Depends(get_db)):
    if not METRICS_FILE.exists():
        raise HTTPException(status_code=503, detail="Evaluation metrics not yet computed. Run scripts/evaluate.py first.")

    with open(METRICS_FILE) as f:
        data = json.load(f)

    counts = await db.execute(
        text("SELECT COUNT(*) FROM products")
    )
    total = counts.scalar_one()

    tagged = await db.execute(
        text("SELECT COUNT(DISTINCT product_id) FROM product_tags")
    )
    tagged_count = tagged.scalar_one()

    return EvaluationMetrics(
        precision=data["precision"],
        recall=data["recall"],
        f1=data["f1"],
        avg_latency_ms=data["avg_latency_ms"],
        p50_latency_ms=data["p50_latency_ms"],
        p95_latency_ms=data["p95_latency_ms"],
        p99_latency_ms=data["p99_latency_ms"],
        total_products=total,
        tagged_products=tagged_count,
        tagging_reduction_pct=data["tagging_reduction_pct"],
        sample_size=data["sample_size"],
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT COUNT(*) FROM products"))
        total = result.scalar_one()
        tagged = await db.execute(text("SELECT COUNT(DISTINCT product_id) FROM product_tags"))
        tagged_count = tagged.scalar_one()
        db_status = "healthy"
    except Exception as exc:
        return HealthResponse(status="degraded", database=str(exc), total_products=0, tagged_products=0)

    return HealthResponse(
        status="ok",
        database=db_status,
        total_products=total,
        tagged_products=tagged_count,
    )
