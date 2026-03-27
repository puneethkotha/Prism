function Arrow({ vertical = false }: { vertical?: boolean }) {
  if (vertical) {
    return (
      <div className="flex flex-col items-center my-1">
        <div className="w-px h-5 bg-gray-200" />
        <svg width="10" height="6" viewBox="0 0 10 6" className="text-gray-300">
          <path d="M0 0L5 6L10 0" fill="currentColor" />
        </svg>
      </div>
    )
  }
  return (
    <div className="flex items-center self-center mx-1 shrink-0">
      <div className="h-px w-6 bg-gray-200" />
      <svg width="6" height="10" viewBox="0 0 6 10" className="text-gray-300">
        <path d="M0 0L6 5L0 10" fill="currentColor" />
      </svg>
    </div>
  )
}

function Node({
  label,
  sub,
  tag,
  accent = 'slate',
}: {
  label: string
  sub?: string
  tag?: string
  accent?: 'slate' | 'indigo' | 'violet' | 'emerald' | 'amber' | 'blue'
}) {
  const tagColor: Record<string, string> = {
    slate:   'bg-slate-100 text-slate-600',
    indigo:  'bg-indigo-50 text-indigo-600',
    violet:  'bg-violet-50 text-violet-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber:   'bg-amber-50 text-amber-600',
    blue:    'bg-blue-50 text-blue-600',
  }
  const dotColor: Record<string, string> = {
    slate:   'bg-slate-400',
    indigo:  'bg-indigo-400',
    violet:  'bg-violet-400',
    emerald: 'bg-emerald-400',
    amber:   'bg-amber-400',
    blue:    'bg-blue-400',
  }
  return (
    <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm min-w-[140px] max-w-[180px]">
      <div className="flex items-center gap-2 mb-1.5">
        <div className={`w-2 h-2 rounded-full shrink-0 ${dotColor[accent]}`} />
        <span className="text-xs font-semibold text-gray-800 leading-tight">{label}</span>
      </div>
      {sub && <p className="text-[11px] text-gray-400 leading-snug pl-4">{sub}</p>}
      {tag && (
        <span className={`mt-2 inline-block text-[10px] font-mono px-1.5 py-0.5 rounded ${tagColor[accent]}`}>
          {tag}
        </span>
      )}
    </div>
  )
}

function PhaseLabel({ label, badge }: { label: string; badge: string }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="text-xs font-mono font-bold text-gray-400 uppercase tracking-widest">{label}</span>
      <span className="text-[10px] bg-gray-100 text-gray-500 rounded-full px-2 py-0.5">{badge}</span>
    </div>
  )
}

function StatPill({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-white border border-gray-100 rounded-lg px-4 py-3 shadow-sm text-center">
      <div className="text-lg font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-400 mt-0.5">{label}</div>
    </div>
  )
}

const STEPS = [
  { num: '01', title: 'Ingest', desc: 'Amazon Reviews 2023 Electronics metadata downloaded from HuggingFace. 25,000 products stored as title + raw_text in PostgreSQL.', accent: 'slate' as const },
  { num: '02', title: 'Extract', desc: 'Claude Sonnet reads each raw_text and outputs structured JSON: category, subcategory, key_features, use_case, target_audience, complexity, sentiment.', accent: 'violet' as const },
  { num: '03', title: 'Embed', desc: 'all-MiniLM-L6-v2 encodes title + tag fields into a 384-dim normalized vector per product. MPS-accelerated; 25K products done in 34 seconds.', accent: 'indigo' as const },
  { num: '04', title: 'Index', desc: 'Vectors stored in pgvector with an ivfflat cosine index (lists=100). Enables approximate nearest-neighbour search inside PostgreSQL with no external vector DB.', accent: 'blue' as const },
  { num: '05', title: 'Serve', desc: 'GET /search encodes the query at request time, runs a single cosine similarity query, and returns top-K results with scores. p95 latency: 7.7ms.', accent: 'emerald' as const },
]

const APIS = [
  { method: 'POST', path: '/extract',         desc: 'LLM extraction on arbitrary text' },
  { method: 'GET',  path: '/search',           desc: 'Semantic search, top-K with similarity scores' },
  { method: 'GET',  path: '/product/{id}',     desc: 'Product record with extracted tags' },
  { method: 'GET',  path: '/metrics',          desc: 'Precision, recall, F1, latency percentiles' },
  { method: 'GET',  path: '/health',           desc: 'DB connectivity and product counts' },
]

export function ArchitectureDiagram() {
  return (
    <section className="py-16 px-4 bg-gray-50 border-t border-gray-100">
      <div className="max-w-5xl mx-auto">

        <h2 className="text-2xl font-bold text-gray-900 mb-1">Pipeline Architecture</h2>
        <p className="text-sm text-gray-500 mb-10">
          Offline batch pipeline runs once to populate the database. Online path handles each search request in real time.
        </p>

        {/* ── OFFLINE PIPELINE ── */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm mb-4">
          <PhaseLabel label="Offline pipeline" badge="runs once" />
          <div className="flex flex-wrap items-center gap-1">
            <Node label="Amazon Reviews 2023" sub="25K Electronics products" tag="HuggingFace" accent="slate" />
            <Arrow />
            <Node label="Tag Extractor" sub="Claude Sonnet or rule-based" tag="POST /extract" accent="violet" />
            <Arrow />
            <Node label="products" sub="id · asin · title · raw_text" tag="PostgreSQL" accent="slate" />
            <Arrow />
            <Node label="product_tags" sub="tags JSONB" tag="PostgreSQL" accent="slate" />
          </div>
          <div className="flex items-start mt-4 ml-[188px] gap-1">
            <div className="flex flex-col items-center">
              <div className="h-6 w-px bg-gray-200" />
              <svg width="10" height="6" viewBox="0 0 10 6" className="text-gray-300"><path d="M0 0L5 6L10 0" fill="currentColor" /></svg>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1 mt-1 ml-40">
            <Node label="all-MiniLM-L6-v2" sub="384-dim sentence encoder" tag="sentence-transformers" accent="indigo" />
            <Arrow />
            <Node label="embedding vector(384)" sub="ivfflat cosine index" tag="pgvector" accent="blue" />
          </div>
        </div>

        {/* ── ONLINE PIPELINE ── */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm mb-4">
          <PhaseLabel label="Online pipeline" badge="p95 = 7.7ms per request" />
          <div className="flex flex-wrap items-center gap-1">
            <Node label="User query" sub="GET /search?q=...&k=10" tag="HTTP" accent="slate" />
            <Arrow />
            <Node label="all-MiniLM-L6-v2" sub="encode query at request time" tag="384-dim" accent="indigo" />
            <Arrow />
            <Node label="pgvector" sub="cosine similarity, top-K" tag="ivfflat" accent="blue" />
            <Arrow />
            <Node label="SearchResponse" sub="results + scores + latency_ms" tag="FastAPI" accent="emerald" />
          </div>
        </div>

        {/* ── EVALUATION ── */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm mb-8">
          <PhaseLabel label="Evaluation" badge="500-item held-out sample" />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatPill value="93.7%" label="Precision" />
            <StatPill value="93.7%" label="Recall" />
            <StatPill value="93.7%" label="F1" />
            <StatPill value="93.7%" label="Tagging reduction" />
          </div>
          <p className="text-xs text-gray-400 mt-3 leading-relaxed">
            Human labels derived from product text using stricter subcategory rules and a broader sentiment keyword set than the tagger.
            Precision = fraction of tags needing no human correction on the held-out sample.
          </p>
        </div>

        {/* ── STEP-BY-STEP + API ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Steps */}
          <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
            <div className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-widest mb-5">Data flow</div>
            <div className="space-y-5">
              {STEPS.map(({ num, title, desc, accent }, i) => {
                const dot: Record<string, string> = {
                  slate:   'bg-slate-400',
                  indigo:  'bg-indigo-400',
                  violet:  'bg-violet-400',
                  emerald: 'bg-emerald-400',
                  blue:    'bg-blue-400',
                }
                return (
                  <div key={num} className="flex gap-3">
                    <div className="flex flex-col items-center shrink-0">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white ${dot[accent]}`}>
                        {num}
                      </div>
                      {i < STEPS.length - 1 && <div className="w-px flex-1 bg-gray-100 mt-1" />}
                    </div>
                    <div className="pb-1">
                      <div className="text-sm font-semibold text-gray-800 mb-1">{title}</div>
                      <div className="text-xs text-gray-500 leading-relaxed">{desc}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* API endpoints */}
          <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
            <div className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-widest mb-5">API endpoints</div>
            <div className="space-y-2">
              {APIS.map(ep => (
                <div key={ep.path} className="flex gap-3 bg-gray-50 rounded-lg px-4 py-3">
                  <span className={`text-xs font-mono font-bold w-10 shrink-0 pt-0.5 ${ep.method === 'POST' ? 'text-amber-500' : 'text-indigo-500'}`}>
                    {ep.method}
                  </span>
                  <div>
                    <div className="text-xs font-mono text-gray-700">{ep.path}</div>
                    <div className="text-[11px] text-gray-400 mt-0.5">{ep.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6">
              <div className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-widest mb-3">Stack</div>
              <div className="space-y-1">
                {[
                  ['LLM', 'Claude Sonnet · Anthropic SDK'],
                  ['Embeddings', 'all-MiniLM-L6-v2 · 384-dim'],
                  ['Vector index', 'pgvector ivfflat · cosine'],
                  ['Backend', 'FastAPI · asyncpg · SQLAlchemy'],
                  ['Frontend', 'React · TypeScript · Tailwind · Vite'],
                ].map(([k, v]) => (
                  <div key={k} className="flex gap-3 text-xs">
                    <span className="text-gray-400 w-28 shrink-0">{k}</span>
                    <span className="text-gray-600">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
