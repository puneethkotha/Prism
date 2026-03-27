import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding import embedding_service
from app.schemas import SearchResult, SearchResponse, ExtractedTags


class SearchService:
    async def semantic_search(
        self, query: str, k: int, db: AsyncSession
    ) -> SearchResponse:
        start = time.perf_counter()
        query_vector = embedding_service.embed(query)
        vector_literal = "[" + ",".join(str(v) for v in query_vector) + "]"

        sql = text("""
            SELECT
                p.id,
                p.asin,
                p.title,
                pt.tags,
                1 - (pt.embedding <=> :query_vec::vector) AS similarity
            FROM product_tags pt
            JOIN products p ON p.id = pt.product_id
            ORDER BY pt.embedding <=> :query_vec::vector
            LIMIT :k
        """)

        result = await db.execute(sql, {"query_vec": vector_literal, "k": k})
        rows = result.fetchall()
        latency_ms = (time.perf_counter() - start) * 1000

        results = []
        for rank, row in enumerate(rows, start=1):
            tags_data = row.tags if isinstance(row.tags, dict) else {}
            try:
                tags = ExtractedTags(**tags_data)
            except Exception:
                tags = ExtractedTags(
                    category=tags_data.get("category", ""),
                    subcategory=tags_data.get("subcategory", ""),
                    key_features=tags_data.get("key_features", []),
                    use_case=tags_data.get("use_case", ""),
                    target_audience=tags_data.get("target_audience", ""),
                    complexity=tags_data.get("complexity", "Beginner"),
                    sentiment=tags_data.get("sentiment", "Neutral"),
                )
            results.append(
                SearchResult(
                    product_id=row.id,
                    asin=row.asin,
                    title=row.title,
                    tags=tags,
                    similarity_score=round(float(row.similarity), 4),
                    rank=rank,
                )
            )

        return SearchResponse(
            query=query,
            results=results,
            latency_ms=round(latency_ms, 2),
            total_results=len(results),
        )


search_service = SearchService()
