"""
Latency verification tests.

Asserts that p95 search latency is under 120ms across 100 queries.
Run after data is loaded and embeddings are generated.
"""

import time
import statistics
import pytest
from httpx import AsyncClient

SEARCH_QUERIES = [
    "wireless bluetooth headphones",
    "gaming laptop RTX GPU",
    "smart home security camera",
    "portable charger USB-C",
    "mechanical keyboard switch",
    "4K monitor ultrawide",
    "fitness tracker heart rate",
    "USB hub multiport",
    "drone camera stabilizer",
    "smart speaker Alexa",
    "true wireless earbuds ANC",
    "standing desk motorized",
    "webcam streaming 1080p",
    "external SSD fast",
    "gaming mouse DPI",
    "VR headset virtual reality",
    "smart thermostat Nest",
    "robot vacuum mapping",
    "electric toothbrush sonic",
    "coffee maker programmable",
]


@pytest.mark.asyncio
async def test_search_latency_p95_under_120ms(client: AsyncClient):
    """
    Verify that p95 end-to-end search latency, including embedding + pgvector query,
    stays under 120ms across 100 queries.
    """
    latencies: list[float] = []

    for i in range(100):
        query = SEARCH_QUERIES[i % len(SEARCH_QUERIES)]
        start = time.perf_counter()
        resp = await client.get("/search", params={"q": query, "k": 10})
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200, f"Search failed for query: {query}"
        latencies.append(elapsed_ms)

    n = len(latencies)
    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[int(n * 0.50)]
    p95 = sorted_latencies[int(n * 0.95)]
    p99 = sorted_latencies[int(n * 0.99)]
    avg = statistics.mean(latencies)

    print(f"\nLatency stats ({n} queries):")
    print(f"  avg: {avg:.1f}ms")
    print(f"  p50: {p50:.1f}ms")
    print(f"  p95: {p95:.1f}ms")
    print(f"  p99: {p99:.1f}ms")

    assert p95 < 120, (
        f"p95 latency {p95:.1f}ms exceeds 120ms target. "
        f"Check pgvector index (ivfflat) and connection pool settings."
    )


@pytest.mark.asyncio
async def test_search_latency_no_cold_start_outliers(client: AsyncClient):
    """Warm up then verify no single query takes over 500ms."""
    # Warm-up
    for query in SEARCH_QUERIES[:3]:
        await client.get("/search", params={"q": query, "k": 10})

    for query in SEARCH_QUERIES:
        start = time.perf_counter()
        resp = await client.get("/search", params={"q": query, "k": 10})
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        assert elapsed_ms < 500, f"Query '{query}' took {elapsed_ms:.1f}ms — unexpected outlier"
