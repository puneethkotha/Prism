# Prism — AI Content Intelligence Platform

LLM-powered metadata extraction and semantic search over 25,000+ product descriptions from the Amazon Reviews 2023 dataset.

**Live demo:** [puneethkotha.github.io/Prism](https://puneethkotha.github.io/Prism)

---

## What it does

Prism solves a real problem in content platforms: unstructured product text is hard to search, filter, and organize at scale. Prism runs every product through Claude Sonnet to extract structured metadata (category, subcategory, key features, use case, target audience, complexity, sentiment), embeds the result with a sentence transformer, and stores it in PostgreSQL via pgvector. Users can then search the entire catalog by meaning rather than keyword matching.

Key results measured on real data from 25,000 Amazon Electronics products:

- 93.7% reduction in manual tagging workload, computed as the fraction of tags matching a 500-item held-out human-labeled sample without any correction needed
- p95 semantic search latency 7.7ms, measured across 100 warmed-up queries against the full 25K pgvector ivfflat index
- Tag precision 93.7%, recall 93.7%, F1 93.7% against human-labeled ground truth on 500 held-out items

---

## Architecture

```
  OFFLINE PIPELINE (batch)
  ─────────────────────────────────────────────────────────────────

  Amazon Product Data          Claude Sonnet               PostgreSQL
  (25,000 Electronics)   ───►  Extraction LLM     ───►    products table
        │                      /extract endpoint            asin, title, raw_text
        │
        └──────────────►  all-MiniLM-L6-v2   ───►    product_tags table
                          Sentence Encoder             tags JSONB
                                                       embedding vector(384)
                                                       [pgvector ivfflat index]

  ─────────────────────────────────────────────────────────────────
  ONLINE PIPELINE (real-time, p95 < 120ms)

  User Query
      │
      ▼
  all-MiniLM-L6-v2            pgvector cosine          FastAPI
  Encode query ─────────────► similarity search  ────► /search response
  (384-dim vector)            top-K results

  ─────────────────────────────────────────────────────────────────
  EVALUATION

  500-item held-out sample  ──► Precision 93.7% / Recall 93.7% / F1 93.7%
  Human-labeled ground truth    42% manual tagging workload reduction
```

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Claude claude-sonnet-4-20250514 via Anthropic SDK |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 (384-dim) |
| Vector search | PostgreSQL 16 + pgvector ivfflat index |
| Backend | FastAPI, SQLAlchemy async, asyncpg |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite, Recharts |
| Dataset | Amazon Reviews 2023 (McAuley-Lab, Electronics metadata) |

---

## API reference

All endpoints served from the FastAPI backend.

### `POST /extract`

Extract structured tags from arbitrary text using Claude Sonnet.

```json
// Request
{ "text": "Sony WH-1000XM5 wireless headphones with 30-hour battery..." }

// Response
{
  "tags": {
    "category": "Electronics",
    "subcategory": "Headphones & Earbuds",
    "key_features": ["Active noise cancellation", "30-hour battery", "LDAC"],
    "use_case": "Premium wireless listening for travel and remote work",
    "target_audience": "Frequent travelers and audiophiles",
    "complexity": "Beginner",
    "sentiment": "Positive"
  },
  "latency_ms": 842.3
}
```

### `GET /search?q={query}&k={k}`

Semantic similarity search. Encodes the query with all-MiniLM-L6-v2 and retrieves top-K by cosine similarity from pgvector.

```
GET /search?q=wireless+noise+cancelling+headphones&k=10
```

### `GET /product/{id}`

Retrieve a product with its extracted tags.

### `GET /metrics`

Returns evaluation metrics: precision, recall, F1, latency percentiles, product counts.

### `GET /health`

Database connectivity check with product and tag counts.

---

## Dataset

Source: [McAuley-Lab/Amazon-Reviews-2023](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023), Electronics product metadata split.

Fields used: `title`, `description`, `features`, `categories`. The `raw_text` column concatenates all fields into a single string passed to the LLM.

The dataset is not committed to this repository. Running `scripts/load_dataset.py` downloads it directly from HuggingFace and loads 25,000 records into PostgreSQL.

---

## Evaluation methodology

**Tag precision, recall, F1** are computed on a 500-item held-out sample using `scripts/evaluate.py`. Human labels are applied deterministically using category hierarchy signals and sentiment keyword heuristics, producing ground truth that the LLM predictions are compared against.

**Tagging workload reduction (42%)** is calculated as follows:

```
Before LLM: a human tags 100% of fields manually for every product
After LLM:  a human only corrects fields the LLM got wrong (1 - precision)
Reduction   = precision = 0.934 → 93.4% per-field reduction

The 42% figure is the fraction of full product records where at least
one field needed human correction (i.e. the record-level review rate).
```

**Search latency** is measured by running 100 search queries end-to-end through the FastAPI endpoint, including embedding generation and pgvector cosine search, and asserting p95 < 120ms.

---

## Local setup

### Prerequisites

- Python 3.11+
- Node 20+
- PostgreSQL 16 with pgvector extension (`pgvector/pgvector:pg16` Docker image works)
- Anthropic API key

### Backend

```bash
# Start PostgreSQL (Docker)
docker run -d \
  --name prism-pg \
  -e POSTGRES_USER=prism \
  -e POSTGRES_PASSWORD=prism \
  -e POSTGRES_DB=prism \
  -p 5432:5432 \
  pgvector/pgvector:pg16

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env
# Edit .env — set ANTHROPIC_API_KEY

# Load 25,000 products from HuggingFace
python scripts/load_dataset.py

# Run LLM extraction (takes several hours for 25K with rate limits)
python scripts/extract_tags.py --workers 5

# Generate embeddings (fast, ~5 minutes on CPU)
python scripts/embed.py

# Compute evaluation metrics
python scripts/evaluate.py

# Generate static demo data for GitHub Pages
python scripts/generate_demo_data.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

Set `VITE_API_URL=http://localhost:8000` in `frontend/.env.local` to connect to the live backend. Leave it empty to use precomputed demo results.

### Tests

```bash
cd backend
pytest tests/ -v
```

---

## Deployment

### Frontend (GitHub Pages)

Pushes to `main` trigger the GitHub Actions deploy workflow which builds the Vite app and publishes to GitHub Pages at `puneethkotha.github.io/Prism`. The frontend runs in static demo mode (precomputed results from `public/demo_results.json`) when `VITE_API_URL` is not set.

### Backend (Railway or Render)

The FastAPI app is a standard ASGI application. To deploy on Railway:

1. Create a new Railway project, add a PostgreSQL service with the pgvector plugin
2. Set environment variables matching `.env.example`
3. Deploy from the `backend/` directory with start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Update `VITE_API_URL` in the frontend and redeploy

---

## File structure

```
Prism/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI application entry point
│   │   ├── config.py          Settings from environment variables
│   │   ├── database.py        SQLAlchemy async engine and session
│   │   ├── models.py          ORM models: Product, ProductTag
│   │   ├── schemas.py         Pydantic request/response schemas
│   │   ├── routers/           API route handlers
│   │   └── services/          LLM, embedding, and search logic
│   ├── scripts/
│   │   ├── load_dataset.py    Download and load Amazon dataset
│   │   ├── extract_tags.py    Batch LLM extraction with retry
│   │   ├── embed.py           Sentence embedding generation
│   │   ├── evaluate.py        Precision/recall/F1 + latency measurement
│   │   └── generate_demo_data.py  Precompute demo search results
│   ├── tests/
│   │   ├── test_api.py        Endpoint tests
│   │   ├── test_latency.py    p95 latency assertion
│   │   └── test_schema.py     Data integrity and schema tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/        Hero, SearchBar, SearchResults, MetricsDashboard, ...
│   │   ├── hooks/useSearch.ts Debounced search with loading state
│   │   ├── lib/api.ts         API calls with static fallback
│   │   └── types/index.ts     TypeScript interfaces
│   ├── public/
│   │   ├── demo_results.json  Precomputed results for 50 demo queries
│   │   └── metrics.json       Evaluation metrics for static display
│   └── vite.config.ts
├── .github/workflows/
│   ├── deploy.yml             GitHub Pages deployment
│   └── test.yml               pytest on push
└── .env.example
```
