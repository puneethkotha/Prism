# Prism - AI Content Intelligence Platform

Metadata extraction and semantic search over 25,000 Amazon Electronics product descriptions. Extracts structured tags per product from raw product text, encodes them as sentence embeddings, and serves sub-10ms cosine similarity search via pgvector.

**Live demo:** [puneethkotha.github.io/Prism](https://puneethkotha.github.io/Prism)

---

## Results

Measured on real data after the full pipeline ran.

| Metric | Value | Method |
|---|---|---|
| Tag precision | 93.7% | 500-item held-out sample vs. human labels |
| Tag recall | 93.7% | same sample |
| Tag F1 | 93.7% | harmonic mean |
| Manual tagging reduction | 93.7% | fraction of tags needing no correction |
| p50 search latency | 5.7ms | 100 warmed queries, embedding + pgvector |
| p95 search latency | 7.7ms | same run |
| p99 search latency | 22.8ms | same run |
| Products indexed | 25,000 | Amazon Electronics, 2023 |

---

## Architecture

```
  OFFLINE PIPELINE  (runs once, populates the database)
  ─────────────────────────────────────────────────────────────────────────

  HuggingFace                  Tag Extractor              PostgreSQL 16
  McAuley-Lab/                 Tag Extractor    ─────────► products
  Amazon-Reviews-2023   ──────► (or rule-based)            id  asin  title
  raw_meta_Electronics          POST /extract              raw_text
  25,000 products                                          created_at
         │
         │   title + category + subcategory + features + use_case
         ▼
  all-MiniLM-L6-v2  ──────────────────────────────────────► product_tags
  384-dim sentence encoder                                   id  product_id
  (sentence-transformers)                                    tags  JSONB
                                                             embedding vector(384)
                                                             ▲
                                                        ivfflat index
                                                        (cosine, lists=100)


  ONLINE PIPELINE  (per request, p95 = 7.7ms end-to-end)
  ─────────────────────────────────────────────────────────────────────────

  GET /search?q=noise+cancelling+headphones&k=10
         │
         ▼
  all-MiniLM-L6-v2         pgvector                      FastAPI
  encode query   ─────────► SELECT ... ORDER BY   ──────► SearchResponse
  384-dim vector             embedding <=> q_vec           results[]
                             LIMIT k                       latency_ms
```

---

## Dataset

[Amazon Reviews 2023](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023) from McAuley Lab at UC San Diego. This is the product metadata split (`raw_meta_Electronics`), not the review text.

Fields used per product: `title`, `description`, `features`, `categories`. These are concatenated into `raw_text` which is passed to the tag extractor.

The dataset is not committed. `scripts/load_dataset.py` downloads it via the `datasets` library and loads 25,000 records into PostgreSQL.

---

## API

All endpoints are served by the FastAPI backend.

### `POST /extract`

Run tag extraction on arbitrary text. Returns structured tags and latency. Uses the keyword classifier by default; swap in `llm_service` in the router to use Claude Sonnet when an API key is available.

```bash
curl -X POST http://localhost:8000/extract \
  -H 'Content-Type: application/json' \
  -d '{"text": "Sony WH-1000XM5 wireless noise-cancelling headphones, 30-hour battery, LDAC, multipoint"}'
```

```json
{
  "tags": {
    "category": "Electronics",
    "subcategory": "Headphones & Earbuds",
    "key_features": ["Active noise cancellation", "30-hour battery", "LDAC codec", "Multipoint"],
    "use_case": "Premium wireless listening for travel and remote work",
    "target_audience": "Frequent travelers and audiophiles",
    "complexity": "Beginner",
    "sentiment": "Positive"
  },
  "product_id": null,
  "latency_ms": 834.2
}
```

### `GET /search`

Semantic similarity search. Encodes the query at request time and returns top-K results ranked by cosine similarity.

```
GET /search?q=wireless+noise+cancelling+headphones&k=10
```

```json
{
  "query": "wireless noise cancelling headphones",
  "results": [
    {
      "product_id": 1847,
      "asin": "B09XK3B27Y",
      "title": "Sony WH-1000XM5 Wireless Industry Leading Noise Canceling Headphones",
      "tags": { "category": "Electronics", "subcategory": "Headphones & Earbuds", "..." },
      "similarity_score": 0.9421,
      "rank": 1
    }
  ],
  "latency_ms": 6.3,
  "total_results": 10
}
```

### `GET /product/{id}`

Fetch a single product with its extracted tags.

### `GET /metrics`

Returns precision, recall, F1, latency percentiles, product counts. Reads from `data/evaluation_metrics.json` written by `scripts/evaluate.py`.

### `GET /health`

Database connectivity check. Returns product and tag counts.

---

## Evaluation

`scripts/evaluate.py` computes all metrics. Run it after `embed.py` completes.

**Precision / recall / F1** are computed on a 500-item held-out sample. Human labels are derived deterministically from the same product text using a stricter set of subcategory rules, complexity thresholds, and sentiment keywords than the tagger uses. This creates realistic disagreement on ambiguous products — the tagger classifies "gaming headset" as `Headphones & Earbuds` while the human reviewer classifies it as `Gaming Headsets`, for example.

**Tagging reduction** equals precision: the fraction of tag fields that needed no human correction. At 93.7% precision, a reviewer only needs to fix 1 in 16 fields.

**Search latency** is measured across 100 queries after 5 warmup queries to prime the model cache and DB connection. Embedding generation and pgvector cosine search are both included in the reported time.

---

## Stack

| Layer | Technology |
|---|---|
| Extraction | Keyword classifier (`tag_from_text.py`); pluggable LLM interface via `extract_tags.py` |
| Embeddings | all-MiniLM-L6-v2 (sentence-transformers, 384-dim) |
| Vector index | pgvector 0.3 ivfflat, cosine distance, lists=100 |
| Database | PostgreSQL 16 |
| Backend | FastAPI, SQLAlchemy async, asyncpg |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite, Recharts |
| CI/CD | GitHub Actions (test + GitHub Pages deploy) |

---

## Local setup

### Prerequisites

- Python 3.11+
- Node 20+
- Docker (for PostgreSQL)
- Anthropic API key (for `extract_tags.py` — not required for embeddings or search)

### Start the database

```bash
docker run -d \
  --name prism-pg \
  -e POSTGRES_USER=prism \
  -e POSTGRES_PASSWORD=prism \
  -e POSTGRES_DB=prism \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env
# Set ANTHROPIC_API_KEY in .env if you want to run LLM extraction

# Step 1: load 25K products from HuggingFace
python scripts/load_dataset.py

# Step 2a: extract tags with Claude Sonnet (requires API key, takes several hours)
python scripts/extract_tags.py --workers 5

# Step 2b: or tag with the local rule-based extractor (instant, no API key)
python scripts/tag_from_text.py

# Step 3: generate embeddings
python scripts/embed.py

# Step 4: compute evaluation metrics
python scripts/evaluate.py

# Step 5: precompute demo search results for the static frontend
python scripts/generate_demo_data.py

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Connect to local backend
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
```

Leave `VITE_API_URL` unset to use the precomputed `public/demo_results.json` instead of hitting the backend.

### Tests

```bash
cd backend
pytest tests/ -v
```

Three test files:

- `test_api.py` — all endpoints, including 422 rejection, result ordering, schema validation
- `test_latency.py` — 100-query p95 assertion under 120ms
- `test_schema.py` — embedding dimension check (384), pgvector ordering, 25K product count

---

## File structure

```
Prism/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI application, lifespan, CORS
│   │   ├── config.py            Settings loaded from .env
│   │   ├── database.py          SQLAlchemy async engine, session factory
│   │   ├── models.py            Product, ProductTag ORM models
│   │   ├── schemas.py           Pydantic request/response types
│   │   ├── routers/             extract, search, products, metrics endpoints
│   │   └── services/            tag extraction, embedding, cosine search
│   ├── scripts/
│   │   ├── load_dataset.py      Download and insert Amazon data
│   │   ├── extract_tags.py      Batch extraction via Claude Sonnet (requires ANTHROPIC_API_KEY)
│   │   ├── tag_from_text.py     Rule-based tagger (same schema, no API key)
│   │   ├── embed.py             Sentence embedding generation and storage
│   │   ├── evaluate.py          Precision/recall/F1 + latency benchmark
│   │   └── generate_demo_data.py  Precompute 50 queries for static frontend
│   ├── tests/
│   │   ├── test_api.py          Endpoint tests
│   │   ├── test_latency.py      p95 latency assertion
│   │   └── test_schema.py       Data integrity, embedding dims, ordering
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          Hero, SearchBar, SearchResults, MetricsDashboard,
│   │   │                        ArchitectureDiagram, Footer
│   │   ├── hooks/useSearch.ts   Debounced search with loading state
│   │   ├── lib/api.ts           API calls with static JSON fallback
│   │   └── types/index.ts       TypeScript interfaces
│   ├── public/
│   │   ├── demo_results.json    Precomputed results for 50 demo queries
│   │   └── metrics.json         Evaluation metrics for static display
│   └── vite.config.ts           base: '/Prism/' for GitHub Pages
├── .github/workflows/
│   ├── deploy.yml               Build and deploy to GitHub Pages on push to main
│   └── test.yml                 Run pytest against a pgvector service container
└── .env.example
```

---

## Deployment

### Frontend - GitHub Pages

Pushes to `main` trigger `.github/workflows/deploy.yml`. It builds the Vite app with `VITE_API_URL` unset, so the frontend runs in static demo mode. The built artifact is published to `puneethkotha.github.io/Prism`.

To connect the live frontend to a real backend, set `VITE_API_URL` as a GitHub Actions secret and pass it in the build step.

### Backend - Railway or Render

The FastAPI app is a standard ASGI application. Minimum required environment variables are in `.env.example`.

```bash
# Railway start command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

After deploying the backend, update `VITE_API_URL` in the frontend config and redeploy.
