"""
Schema validation and data integrity tests.

Verifies that stored tags conform to the ExtractedTags schema
and that pgvector returns correctly ordered top-K results.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from app.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_all_tags_have_required_fields(client: AsyncClient):
    """Spot-check 50 products to verify stored JSONB tags have all required fields."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT tags FROM product_tags ORDER BY RANDOM() LIMIT 50")
        )
        rows = result.fetchall()

    required_fields = {"category", "subcategory", "key_features", "use_case", "target_audience", "complexity", "sentiment"}
    valid_complexity = {"Beginner", "Intermediate", "Advanced"}
    valid_sentiment = {"Positive", "Neutral", "Negative"}

    for row in rows:
        tags = row[0]
        missing = required_fields - tags.keys()
        assert not missing, f"Tags missing fields: {missing}. Tags: {tags}"
        assert tags["complexity"] in valid_complexity, f"Invalid complexity: {tags['complexity']}"
        assert tags["sentiment"] in valid_sentiment, f"Invalid sentiment: {tags['sentiment']}"
        assert isinstance(tags["key_features"], list), "key_features must be a list"


@pytest.mark.asyncio
async def test_embeddings_are_correct_dimension():
    """Verify stored embeddings have dimension 384 (all-MiniLM-L6-v2)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT vector_dims(embedding) AS dims FROM product_tags WHERE embedding IS NOT NULL LIMIT 10")
        )
        rows = result.fetchall()

    assert len(rows) > 0, "No embeddings found — run scripts/embed.py first"
    for row in rows:
        assert row[0] == 384, f"Expected 384-dim embeddings, got {row[0]}"


@pytest.mark.asyncio
async def test_pgvector_top_k_ordering():
    """Verify pgvector returns results in descending cosine similarity order."""
    async with AsyncSessionLocal() as db:
        # Pick a random embedding as the query vector
        probe = await db.execute(
            text("SELECT embedding FROM product_tags WHERE embedding IS NOT NULL LIMIT 1")
        )
        row = probe.fetchone()
        assert row is not None, "No embeddings found"
        vec = row[0]
        vec_str = str(vec)

        result = await db.execute(
            text("""
                SELECT 1 - (embedding <=> :q::vector) AS sim
                FROM product_tags
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :q::vector
                LIMIT 20
            """),
            {"q": vec_str},
        )
        similarities = [r[0] for r in result.fetchall()]

    assert similarities[0] >= 0.999, "Top result should be ~1.0 similarity with itself"
    for i in range(len(similarities) - 1):
        assert similarities[i] >= similarities[i + 1], (
            f"Results not in descending order at position {i}: {similarities[i]} < {similarities[i+1]}"
        )


@pytest.mark.asyncio
async def test_product_count_is_25k_or_more():
    """Verify at least 25,000 products were loaded."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT COUNT(*) FROM products"))
        count = result.scalar_one()
    assert count >= 25_000, f"Expected at least 25,000 products, got {count}"


@pytest.mark.asyncio
async def test_tagged_product_count():
    """Verify a significant fraction of products have tags and embeddings."""
    async with AsyncSessionLocal() as db:
        total = (await db.execute(text("SELECT COUNT(*) FROM products"))).scalar_one()
        tagged = (await db.execute(text("SELECT COUNT(*) FROM product_tags WHERE embedding IS NOT NULL"))).scalar_one()

    fraction = tagged / total
    assert fraction >= 0.95, f"Only {fraction:.1%} of products tagged. Expected >=95%."
