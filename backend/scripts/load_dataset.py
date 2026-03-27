"""
Download and load 25,000 product records from the Amazon Reviews 2023 dataset
(Electronics metadata) into PostgreSQL.

Usage:
    python scripts/load_dataset.py
"""

import os
import sys
import json
import logging
from pathlib import Path

import psycopg2
from datasets import load_dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

TARGET_COUNT = 25_000
CATEGORY = "Electronics"


def build_raw_text(item: dict) -> str:
    parts = []
    if item.get("title"):
        parts.append(item["title"])
    desc = item.get("description") or []
    if isinstance(desc, list):
        parts.extend(desc)
    elif isinstance(desc, str):
        parts.append(desc)
    features = item.get("features") or []
    if isinstance(features, list):
        parts.extend(features)
    cats = item.get("categories") or []
    if isinstance(cats, list):
        parts.extend(cats)
    return " ".join(str(p) for p in parts if p).strip()


def main():
    log.info("Connecting to PostgreSQL...")
    conn = psycopg2.connect(settings.database_url_sync)
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            asin VARCHAR(20) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            raw_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_tags (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            tags JSONB NOT NULL,
            embedding vector(384),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS product_tags_embedding_idx ON product_tags USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
    conn.commit()
    log.info("Schema ready.")

    cur.execute("SELECT COUNT(*) FROM products")
    existing = cur.fetchone()[0]
    if existing >= TARGET_COUNT:
        log.info(f"Already have {existing} products. Skipping load.")
        cur.close()
        conn.close()
        return

    log.info(f"Loading {CATEGORY} metadata from HuggingFace...")
    dataset = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_meta_{CATEGORY}",
        split="full",
        trust_remote_code=True,
    )

    log.info(f"Dataset size: {len(dataset)}. Inserting up to {TARGET_COUNT} records...")
    inserted = 0
    batch = []
    batch_size = 500

    for item in tqdm(dataset, total=min(TARGET_COUNT * 2, len(dataset))):
        if inserted >= TARGET_COUNT:
            break

        asin = item.get("parent_asin") or item.get("asin") or ""
        title = item.get("title") or ""
        if not asin or not title or len(title) < 5:
            continue

        desc_raw = item.get("description") or []
        if isinstance(desc_raw, list):
            description = " ".join(str(d) for d in desc_raw if d)
        else:
            description = str(desc_raw) if desc_raw else None

        raw_text = build_raw_text(item)
        if len(raw_text) < 20:
            continue

        batch.append((asin, title[:500], description[:2000] if description else None, raw_text[:5000]))

        if len(batch) >= batch_size:
            cur.executemany(
                """
                INSERT INTO products (asin, title, description, raw_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (asin) DO NOTHING
                """,
                batch,
            )
            conn.commit()
            cur.execute("SELECT COUNT(*) FROM products")
            inserted = cur.fetchone()[0]
            batch = []
            log.info(f"Inserted so far: {inserted}")

    if batch:
        cur.executemany(
            "INSERT INTO products (asin, title, description, raw_text) VALUES (%s, %s, %s, %s) ON CONFLICT (asin) DO NOTHING",
            batch,
        )
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM products")
    final = cur.fetchone()[0]
    log.info(f"Load complete. Total products in DB: {final}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
