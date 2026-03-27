"""
Tests for all FastAPI endpoints.

Requires a running PostgreSQL instance with data loaded.
Run: pytest tests/test_api.py -v
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "total_products" in data
    assert "tagged_products" in data


@pytest.mark.asyncio
async def test_health_reports_product_count(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_products"] >= 25_000, (
        f"Expected at least 25,000 products, got {data['total_products']}"
    )


@pytest.mark.asyncio
async def test_search_returns_results(client: AsyncClient):
    resp = await client.get("/search", params={"q": "wireless headphones", "k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] == 5
    assert len(data["results"]) == 5
    assert data["query"] == "wireless headphones"
    assert data["latency_ms"] > 0


@pytest.mark.asyncio
async def test_search_result_schema(client: AsyncClient):
    resp = await client.get("/search", params={"q": "laptop gaming", "k": 3})
    assert resp.status_code == 200
    data = resp.json()
    for result in data["results"]:
        assert "product_id" in result
        assert "title" in result
        assert "tags" in result
        assert "similarity_score" in result
        assert 0.0 <= result["similarity_score"] <= 1.0
        tags = result["tags"]
        assert "category" in tags
        assert "subcategory" in tags
        assert isinstance(tags["key_features"], list)
        assert "use_case" in tags
        assert "target_audience" in tags
        assert tags["complexity"] in ("Beginner", "Intermediate", "Advanced")
        assert tags["sentiment"] in ("Positive", "Neutral", "Negative")


@pytest.mark.asyncio
async def test_search_results_ordered_by_similarity(client: AsyncClient):
    resp = await client.get("/search", params={"q": "bluetooth speaker", "k": 10})
    assert resp.status_code == 200
    results = resp.json()["results"]
    scores = [r["similarity_score"] for r in results]
    assert scores == sorted(scores, reverse=True), "Results should be ordered by descending similarity"


@pytest.mark.asyncio
async def test_search_top_k_respected(client: AsyncClient):
    for k in (1, 5, 20):
        resp = await client.get("/search", params={"q": "camera", "k": k})
        assert resp.status_code == 200
        assert resp.json()["total_results"] == k


@pytest.mark.asyncio
async def test_search_query_too_short_rejected(client: AsyncClient):
    resp = await client.get("/search", params={"q": "a"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_product_by_id_exists(client: AsyncClient):
    # Get a valid product id from search first
    search_resp = await client.get("/search", params={"q": "keyboard", "k": 1})
    assert search_resp.status_code == 200
    product_id = search_resp.json()["results"][0]["product_id"]

    resp = await client.get(f"/product/{product_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == product_id
    assert len(data["title"]) > 0
    assert data["tags"] is not None


@pytest.mark.asyncio
async def test_product_not_found(client: AsyncClient):
    resp = await client.get("/product/99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    resp = await client.get("/metrics")
    # Either 200 (metrics file exists) or 503 (not yet computed)
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert 0 < data["precision"] <= 1
        assert 0 < data["recall"] <= 1
        assert 0 < data["f1"] <= 1
        assert data["avg_latency_ms"] > 0
        assert data["total_products"] >= 25_000


@pytest.mark.asyncio
async def test_extract_returns_valid_schema(client: AsyncClient):
    text = (
        "Sony WH-1000XM5 wireless noise-cancelling headphones with 30-hour battery, "
        "LDAC support for high-res audio, multipoint connection for two devices, "
        "and Alexa/Google Assistant integration. Foldable design for portability."
    )
    resp = await client.post("/extract", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert "tags" in data
    tags = data["tags"]
    required_fields = {"category", "subcategory", "key_features", "use_case", "target_audience", "complexity", "sentiment"}
    assert required_fields.issubset(tags.keys())
    assert isinstance(tags["key_features"], list)
    assert tags["complexity"] in ("Beginner", "Intermediate", "Advanced")
    assert tags["sentiment"] in ("Positive", "Neutral", "Negative")
    assert data["latency_ms"] > 0


@pytest.mark.asyncio
async def test_extract_rejects_short_text(client: AsyncClient):
    resp = await client.post("/extract", json={"text": "short"})
    assert resp.status_code == 422
