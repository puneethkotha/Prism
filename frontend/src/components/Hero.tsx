export function Hero() {
  return (
    <section className="pt-20 pb-16 px-4">
      <div className="max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 bg-prism-50 border border-prism-200 rounded-full px-4 py-1.5 text-sm text-prism-700 font-medium mb-6">
          <span className="w-2 h-2 bg-prism-500 rounded-full animate-pulse" />
          25,000+ products indexed
        </div>

        <h1 className="text-5xl font-bold text-gray-900 tracking-tight mb-4">
          Prism
        </h1>
        <p className="text-xl text-prism-600 font-semibold mb-4">
          AI Content Intelligence Platform
        </p>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed">
          Tag extraction and semantic search over 25,000 Amazon product listings.
          93.7% accuracy against human labels, p95 search at 7.7ms.
        </p>

        <div className="flex flex-wrap justify-center gap-3">
          {[
            { label: 'Tag Extractor', sub: 'Keyword classifier' },
            { label: 'pgvector', sub: 'Vector DB' },
            { label: 'all-MiniLM-L6-v2', sub: 'Embeddings' },
            { label: 'FastAPI', sub: 'Backend' },
            { label: 'PostgreSQL', sub: 'Storage' },
          ].map(badge => (
            <div key={badge.label} className="bg-white border border-gray-200 rounded-lg px-4 py-2 text-center shadow-sm">
              <div className="text-sm font-semibold text-gray-800">{badge.label}</div>
              <div className="text-xs text-gray-400">{badge.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
