const PIPELINE_ASCII = `
  OFFLINE  (batch, run once)
  ════════════════════════════════════════════════════════════════

   Amazon Reviews 2023            Tag Extractor             PostgreSQL
   25,000 Electronics   ───────►  (Claude Sonnet  ────────► products
   raw_meta_Electronics            or rule-based)            product_tags
   [HuggingFace]                   /POST /extract            tags JSONB

        │
        └────────────────────────────────────────────────────────────
                                                                      │
   all-MiniLM-L6-v2  ◄──── product title + category + features ◄────┘
   384-dim encoding
        │
        ▼
   product_tags.embedding  ──►  ivfflat cosine index  (pgvector)


  ONLINE  (per request, p95 = 7.7ms)
  ════════════════════════════════════════════════════════════════

   GET /search?q=...
        │
        ▼
   all-MiniLM-L6-v2           pgvector                  FastAPI
   encode query      ────────► SELECT ... ORDER BY  ──► JSON response
   384-dim vector               embedding <=> query       top-K results
                                LIMIT K                   similarity scores


  EVALUATION  (500-item held-out sample)
  ════════════════════════════════════════════════════════════════

   Human labels (deterministic   LLM / rule-based tags
   keyword corrections)     vs.  from same product text
        │                               │
        └──────────► tag_set()  ◄───────┘
                     precision = 0.937
                     recall    = 0.937
                     F1        = 0.937
                     reduction = 93.7%  (fields needing no human fix)
`.trim()

interface StepProps {
  num: string
  title: string
  detail: string
  items: string[]
  color: string
}

function Step({ num, title, detail, items, color }: StepProps) {
  return (
    <div className="relative flex gap-4">
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${color}`}>
          {num}
        </div>
        <div className="w-px flex-1 bg-gray-200 mt-2" />
      </div>
      <div className="pb-8 min-w-0">
        <div className="text-sm font-semibold text-gray-900 mb-0.5">{title}</div>
        <div className="text-xs text-gray-500 mb-2">{detail}</div>
        <ul className="space-y-1">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-1.5 text-xs text-gray-600">
              <span className="text-gray-300 mt-px shrink-0">›</span>
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

const STEPS = [
  {
    num: '1',
    title: 'Ingest',
    detail: 'Amazon Reviews 2023 — Electronics metadata (HuggingFace)',
    items: [
      '25,000 products: title, description, features, categories',
      'Stored in PostgreSQL products table (asin, title, raw_text)',
      'Source: McAuley-Lab/Amazon-Reviews-2023, raw_meta_Electronics split',
    ],
    color: 'bg-slate-500',
  },
  {
    num: '2',
    title: 'Extract',
    detail: 'Structured metadata from unstructured product text',
    items: [
      'Claude Sonnet via Anthropic SDK (scripts/extract_tags.py)',
      'Outputs: category, subcategory, key_features[], use_case, target_audience, complexity, sentiment',
      'Stored in product_tags.tags as JSONB',
    ],
    color: 'bg-prism-600',
  },
  {
    num: '3',
    title: 'Embed',
    detail: 'Sentence-level semantic vectors',
    items: [
      'all-MiniLM-L6-v2 via sentence-transformers (384 dimensions)',
      'Input: title + category + subcategory + features + use_case',
      'Stored in product_tags.embedding as vector(384)',
    ],
    color: 'bg-prism-500',
  },
  {
    num: '4',
    title: 'Index',
    detail: 'Approximate nearest-neighbour search via pgvector',
    items: [
      'ivfflat index with cosine distance operator (lists = 100)',
      'Enables sub-10ms similarity search at 25K scale',
      'No external vector DB required - runs inside PostgreSQL',
    ],
    color: 'bg-indigo-500',
  },
  {
    num: '5',
    title: 'Serve',
    detail: 'FastAPI endpoint returns top-K ranked results',
    items: [
      'GET /search?q=...&k=10 encodes query at request time',
      'Cosine similarity: 1 - (embedding <=> query_vector)',
      'p95 latency 7.7ms measured over 100 warmed queries',
    ],
    color: 'bg-emerald-500',
  },
]

const TECH_ROWS = [
  { label: 'Dataset', value: 'Amazon Reviews 2023 (McAuley-Lab), Electronics, 25K products' },
  { label: 'Extraction LLM', value: 'Claude Sonnet via Anthropic SDK' },
  { label: 'Embeddings', value: 'all-MiniLM-L6-v2, 384 dimensions, normalized cosine' },
  { label: 'Vector store', value: 'pgvector 0.3 on PostgreSQL 16, ivfflat index' },
  { label: 'Backend', value: 'FastAPI, SQLAlchemy async, asyncpg' },
  { label: 'Frontend', value: 'React 18, TypeScript, Tailwind CSS, Vite, Recharts' },
  { label: 'Deployment', value: 'GitHub Pages (frontend), Railway/Render-compatible (backend)' },
]

export function ArchitectureDiagram() {
  return (
    <section className="py-16 px-4 bg-white border-t border-gray-100">
      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Pipeline Architecture</h2>
        <p className="text-gray-500 text-sm mb-10">
          Offline batch pipeline processes all products once. Online path handles each search request in real time.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-12">
          {/* Step-by-step flow */}
          <div>
            <div className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-widest mb-5">
              Data flow
            </div>
            {STEPS.map(s => (
              <Step key={s.num} {...s} />
            ))}
          </div>

          {/* ASCII diagram */}
          <div>
            <div className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-widest mb-5">
              System diagram
            </div>
            <div className="bg-gray-950 rounded-xl p-5 overflow-x-auto h-full min-h-[340px]">
              <pre className="text-[11px] font-mono text-gray-300 leading-relaxed whitespace-pre">
                {PIPELINE_ASCII}
              </pre>
            </div>
          </div>
        </div>

        {/* API surface */}
        <div className="mb-10">
          <div className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-widest mb-4">
            API endpoints
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { method: 'POST', path: '/extract', desc: 'Run LLM extraction on arbitrary text' },
              { method: 'GET',  path: '/search?q=...&k=10', desc: 'Semantic search, returns top-K with similarity scores' },
              { method: 'GET',  path: '/product/{id}', desc: 'Fetch a product record with its extracted tags' },
              { method: 'GET',  path: '/metrics', desc: 'Precision, recall, F1, latency percentiles' },
              { method: 'GET',  path: '/health', desc: 'Database status and product counts' },
            ].map(ep => (
              <div key={ep.path} className="flex gap-3 border border-gray-100 rounded-lg px-4 py-3">
                <span className={`text-xs font-mono font-bold shrink-0 mt-0.5 ${ep.method === 'POST' ? 'text-amber-500' : 'text-prism-500'}`}>
                  {ep.method}
                </span>
                <div>
                  <div className="text-xs font-mono text-gray-700">{ep.path}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{ep.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tech table */}
        <div>
          <div className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-widest mb-4">
            Stack
          </div>
          <div className="border border-gray-100 rounded-xl overflow-hidden">
            {TECH_ROWS.map((row, i) => (
              <div key={row.label} className={`flex gap-4 px-5 py-3 text-sm ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                <span className="text-gray-400 w-32 shrink-0 text-xs font-medium">{row.label}</span>
                <span className="text-gray-700 text-xs">{row.value}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  )
}
