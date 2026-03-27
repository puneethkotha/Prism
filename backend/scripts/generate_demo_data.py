"""
Generate precomputed search results for 50 demo queries for the GitHub Pages static demo.

This script queries the live database and saves results to frontend/public/demo_results.json.
Run this after extract_tags.py and embed.py have completed.

Usage:
    python scripts/generate_demo_data.py
"""

import sys
import json
import logging
from pathlib import Path

import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DEMO_QUERIES = [
    "wireless bluetooth headphones noise cancelling",
    "laptop gaming high performance RTX",
    "smart home security camera wifi night vision",
    "portable battery charger fast charging USB-C",
    "mechanical keyboard RGB gaming",
    "4K monitor ultrawide curved display",
    "fitness tracker heart rate GPS",
    "USB-C hub multiport adapter",
    "drone camera stabilization 4K",
    "smart speaker voice assistant Alexa",
    "wireless earbuds true wireless",
    "standing desk motorized height adjustable",
    "webcam 1080p streaming",
    "external SSD portable fast transfer",
    "gaming mouse high DPI",
    "VR headset virtual reality",
    "smart thermostat energy saving",
    "robot vacuum cleaner mapping",
    "electric toothbrush sonic",
    "coffee maker programmable smart",
    "air purifier HEPA filter",
    "LED desk lamp adjustable brightness",
    "portable projector mini",
    "action camera waterproof 4K",
    "wireless charging pad fast",
    "Bluetooth speaker waterproof outdoor",
    "graphics card GPU",
    "RAM memory DDR5 gaming",
    "CPU cooler liquid cooling",
    "NVMe SSD M.2 fast",
    "network attached storage NAS",
    "mesh wifi router system",
    "power strip surge protector USB",
    "monitor arm ergonomic dual",
    "ergonomic mouse vertical",
    "keyboard wrist rest mechanical",
    "cable management desk organizer",
    "HDMI switch 4K",
    "stream deck studio controller",
    "capture card gaming streaming",
    "microphone condenser recording",
    "studio headphones mixing",
    "turntable vinyl record player",
    "bookshelf speakers stereo",
    "subwoofer home theater",
    "smart bulb LED color changing",
    "smart plug energy monitoring",
    "video doorbell camera",
    "tablet drawing pad stylus",
    "e-reader waterproof backlight",
]

OUTPUT_FILE = Path(__file__).parent.parent.parent / "frontend" / "public" / "demo_results.json"


def search(cur, model: SentenceTransformer, query: str, k: int = 8) -> list[dict]:
    vec = model.encode(query, normalize_embeddings=True)
    vec_str = "[" + ",".join(f"{v:.8f}" for v in vec.tolist()) + "]"
    cur.execute("""
        SELECT
            p.id,
            p.asin,
            p.title,
            pt.tags,
            1 - (pt.embedding <=> %s::vector) AS similarity
        FROM product_tags pt
        JOIN products p ON p.id = pt.product_id
        ORDER BY pt.embedding <=> %s::vector
        LIMIT %s
    """, (vec_str, vec_str, k))
    rows = cur.fetchall()
    results = []
    for rank, row in enumerate(rows, start=1):
        results.append({
            "product_id": row["id"],
            "asin": row["asin"],
            "title": row["title"],
            "tags": row["tags"],
            "similarity_score": round(float(row["similarity"]), 4),
            "rank": rank,
        })
    return results


def main():
    conn = psycopg2.connect(settings.psycopg2_dsn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT COUNT(*) FROM product_tags WHERE embedding IS NOT NULL")
    count = cur.fetchone()[0]
    log.info(f"Products with embeddings: {count}")

    log.info(f"Loading model: {settings.embedding_model}")
    model = SentenceTransformer(settings.embedding_model)

    demo_data = {}
    for query in DEMO_QUERIES:
        log.info(f"Query: {query}")
        results = search(cur, model, query)
        demo_data[query] = results

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(demo_data, f, indent=2)

    log.info(f"Saved demo data for {len(demo_data)} queries to {OUTPUT_FILE}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
