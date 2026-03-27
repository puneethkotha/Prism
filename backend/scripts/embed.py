"""
Generate sentence embeddings for all tagged products and store them in pgvector.

Uses all-MiniLM-L6-v2 (384-dim) from sentence-transformers.
Processes in batches of 512 to maximize GPU/CPU throughput.

Usage:
    python scripts/embed.py [--batch-size N]
"""

import sys
import json
import logging
import argparse
from pathlib import Path

import psycopg2
import psycopg2.extras
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def text_for_embedding(title: str, tags: dict) -> str:
    features = " ".join(tags.get("key_features", []))
    return f"{title} {tags.get('category', '')} {tags.get('subcategory', '')} {features} {tags.get('use_case', '')}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()

    conn = psycopg2.connect(settings.database_url_sync)
    cur = conn.cursor()

    cur.execute("""
        SELECT pt.id, p.title, pt.tags
        FROM product_tags pt
        JOIN products p ON p.id = pt.product_id
        WHERE pt.embedding IS NULL
        ORDER BY pt.id
    """)
    rows = cur.fetchall()
    log.info(f"Found {len(rows)} product_tags without embeddings.")

    if not rows:
        log.info("All embeddings already generated.")
        cur.close()
        conn.close()
        return

    log.info(f"Loading model: {settings.embedding_model}")
    model = SentenceTransformer(settings.embedding_model)

    ids = [r[0] for r in rows]
    texts = [text_for_embedding(r[1], r[2]) for r in rows]

    log.info("Generating embeddings...")
    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    log.info("Writing embeddings to database...")
    write_cur = conn.cursor()
    batch = []
    for tag_id, vec in tqdm(zip(ids, embeddings), total=len(ids), desc="Upserting"):
        vec_str = "[" + ",".join(f"{v:.8f}" for v in vec.tolist()) + "]"
        batch.append((vec_str, tag_id))

        if len(batch) >= 1000:
            write_cur.executemany(
                "UPDATE product_tags SET embedding = %s::vector WHERE id = %s",
                batch,
            )
            conn.commit()
            batch = []

    if batch:
        write_cur.executemany(
            "UPDATE product_tags SET embedding = %s::vector WHERE id = %s",
            batch,
        )
        conn.commit()

    write_cur.close()
    cur.close()
    conn.close()
    log.info(f"Done. Updated {len(ids)} embeddings.")


if __name__ == "__main__":
    main()
