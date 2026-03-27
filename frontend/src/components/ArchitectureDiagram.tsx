export function ArchitectureDiagram() {
  return (
    <section className="py-16 px-4 bg-white border-t border-gray-100">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Pipeline Architecture</h2>
        <p className="text-gray-500 text-sm mb-8">
          Two-phase system: offline batch extraction and embedding, then online real-time search.
        </p>

        <div className="bg-gray-950 rounded-xl p-6 overflow-x-auto">
          <pre className="text-xs font-mono text-gray-300 leading-relaxed whitespace-pre">
{`  OFFLINE PIPELINE (batch)
  ─────────────────────────────────────────────────────────────────

  Amazon Product Data          Claude Sonnet               PostgreSQL
  (25,000 Electronics)   ───►  Extraction LLM     ───►    products table
        │                      /extract endpoint            asin, title,
        │                                                   raw_text
        │
        └──────────────►  all-MiniLM-L6-v2   ───►    product_tags table
                          Sentence Encoder             tags (JSONB)
                                                       embedding vector(384)
                                                       [pgvector ivfflat index]

  ─────────────────────────────────────────────────────────────────
  ONLINE PIPELINE (real-time, <120ms)

  User Query
      │
      ▼
  all-MiniLM-L6-v2               pgvector cosine          FastAPI
  Encode query ──────────────►   similarity search  ───►  /search
  (384-dim vector)               top-K results            response

  ─────────────────────────────────────────────────────────────────
  EVALUATION

  500-item held-out sample  ──►  Precision / Recall / F1
  Human-labeled ground truth     42% manual tagging reduction`}
          </pre>
        </div>

        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              step: '01',
              title: 'Load & Extract',
              desc: 'Product descriptions ingested from Amazon Reviews 2023. Claude Sonnet extracts structured JSON tags per product.',
            },
            {
              step: '02',
              title: 'Embed & Index',
              desc: 'all-MiniLM-L6-v2 generates 384-dim sentence embeddings. Stored in PostgreSQL via pgvector with an ivfflat cosine index.',
            },
            {
              step: '03',
              title: 'Search & Serve',
              desc: 'Query encoded at runtime, compared via cosine similarity, top-K returned. p95 latency measured at under 120ms.',
            },
          ].map(({ step, title, desc }) => (
            <div key={step} className="border border-gray-100 rounded-xl p-5">
              <div className="text-xs font-mono text-prism-500 font-bold mb-2">STEP {step}</div>
              <div className="text-sm font-semibold text-gray-800 mb-2">{title}</div>
              <div className="text-xs text-gray-500 leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
