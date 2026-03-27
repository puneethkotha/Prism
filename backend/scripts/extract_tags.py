"""
Batch LLM metadata extraction for all products without tags.

Uses the Anthropic API to extract structured tags for each product.
Implements exponential-backoff retry and rate limiting to stay within API limits.

Usage:
    python scripts/extract_tags.py [--limit N] [--workers N]

Options:
    --limit     Max products to process (default: all untagged)
    --workers   Concurrent API workers (default: 5)
"""

import sys
import json
import time
import logging
import argparse
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract structured metadata from the following product description. Return only valid JSON with these exact fields:

{
  "category": "top-level product category",
  "subcategory": "specific subcategory",
  "key_features": ["up to 5 key features"],
  "use_case": "primary use case in one sentence",
  "target_audience": "who this product is for",
  "complexity": "one of: Beginner, Intermediate, Advanced",
  "sentiment": "one of: Positive, Neutral, Negative"
}

Product text:
{text}

Return only the JSON object."""

_rate_lock = threading.Semaphore(5)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=3, max=60),
    retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
)
def extract_one(client: anthropic.Anthropic, product_id: int, raw_text: str) -> tuple[int, dict, float]:
    with _rate_lock:
        start = time.perf_counter()
        message = client.messages.create(
            model=settings.llm_model,
            max_tokens=512,
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(text=raw_text[:3000])}],
        )
        latency_ms = (time.perf_counter() - start) * 1000

    raw = message.content[0].text.strip()
    data = json.loads(raw)
    required = {"category", "subcategory", "key_features", "use_case", "target_audience", "complexity", "sentiment"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing fields in LLM response: {missing}")
    if not isinstance(data["key_features"], list):
        data["key_features"] = [data["key_features"]]
    return product_id, data, latency_ms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()

    conn = psycopg2.connect(settings.psycopg2_dsn)
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.raw_text
        FROM products p
        LEFT JOIN product_tags pt ON pt.product_id = p.id
        WHERE pt.id IS NULL
        ORDER BY p.id
        LIMIT %s
    """, (args.limit,))
    rows = cur.fetchall()
    log.info(f"Found {len(rows)} untagged products to process.")

    if not rows:
        log.info("All products already tagged.")
        cur.close()
        conn.close()
        return

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    latencies = []
    success = 0
    failed = 0

    def process(row):
        product_id, raw_text = row
        try:
            return extract_one(client, product_id, raw_text)
        except Exception as exc:
            log.warning(f"Failed product {product_id}: {exc}")
            return None

    write_conn = psycopg2.connect(settings.psycopg2_dsn)
    write_cur = write_conn.cursor()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process, row): row[0] for row in rows}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Extracting"):
            result = future.result()
            if result is None:
                failed += 1
                continue
            product_id, tags, latency_ms = result
            write_cur.execute(
                """
                INSERT INTO product_tags (product_id, tags)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (product_id, json.dumps(tags)),
            )
            write_conn.commit()
            latencies.append(latency_ms)
            success += 1

            if success % 100 == 0:
                log.info(f"Progress: {success} tagged, {failed} failed")

    write_cur.close()
    write_conn.close()
    cur.close()
    conn.close()

    if latencies:
        import statistics
        log.info(f"Done. Tagged: {success}, Failed: {failed}")
        log.info(f"LLM latency — avg: {statistics.mean(latencies):.1f}ms, p95: {sorted(latencies)[int(len(latencies)*0.95)]:.1f}ms")


if __name__ == "__main__":
    main()
