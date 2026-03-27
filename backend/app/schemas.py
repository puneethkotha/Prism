from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ExtractedTags(BaseModel):
    category: str
    subcategory: str
    key_features: list[str]
    use_case: str
    target_audience: str
    complexity: str
    sentiment: str


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    product_id: int | None = None


class ExtractResponse(BaseModel):
    tags: ExtractedTags
    product_id: int | None
    latency_ms: float


class SearchResult(BaseModel):
    product_id: int
    asin: str
    title: str
    tags: ExtractedTags
    similarity_score: float
    rank: int


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    latency_ms: float
    total_results: int


class ProductResponse(BaseModel):
    id: int
    asin: str
    title: str
    description: str | None
    raw_text: str
    tags: ExtractedTags | None
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_products: int
    tagged_products: int
    tagging_reduction_pct: float
    sample_size: int


class HealthResponse(BaseModel):
    status: str
    database: str
    total_products: int
    tagged_products: int
