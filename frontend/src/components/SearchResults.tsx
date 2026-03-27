import type { SearchResponse, SearchResult } from '../types'

const COMPLEXITY_COLOR: Record<string, string> = {
  Beginner: 'bg-green-100 text-green-700',
  Intermediate: 'bg-yellow-100 text-yellow-700',
  Advanced: 'bg-red-100 text-red-700',
}

const SENTIMENT_COLOR: Record<string, string> = {
  Positive: 'bg-emerald-100 text-emerald-700',
  Neutral: 'bg-gray-100 text-gray-600',
  Negative: 'bg-rose-100 text-rose-700',
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-prism-500 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-gray-500 w-10 text-right">{pct}%</span>
    </div>
  )
}

function ResultCard({ result }: { result: SearchResult }) {
  const { tags } = result
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <span className="text-xs font-mono text-gray-400 mr-2">#{result.rank}</span>
          <h3 className="inline text-sm font-semibold text-gray-900 leading-snug">
            {result.title}
          </h3>
        </div>
      </div>

      <ScoreBar score={result.similarity_score} />

      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className="text-xs bg-prism-50 text-prism-700 border border-prism-100 rounded px-2 py-0.5 font-medium">
          {tags.category}
        </span>
        <span className="text-xs bg-gray-50 text-gray-600 border border-gray-200 rounded px-2 py-0.5">
          {tags.subcategory}
        </span>
        <span className={`text-xs rounded px-2 py-0.5 ${COMPLEXITY_COLOR[tags.complexity] ?? 'bg-gray-100 text-gray-600'}`}>
          {tags.complexity}
        </span>
        <span className={`text-xs rounded px-2 py-0.5 ${SENTIMENT_COLOR[tags.sentiment] ?? 'bg-gray-100 text-gray-600'}`}>
          {tags.sentiment}
        </span>
      </div>

      {tags.key_features.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {tags.key_features.slice(0, 4).map((f, i) => (
            <span key={i} className="text-xs text-gray-500 bg-gray-50 rounded px-1.5 py-0.5">
              {f}
            </span>
          ))}
        </div>
      )}

      <p className="mt-2 text-xs text-gray-400 line-clamp-1">
        {tags.use_case}
      </p>
    </div>
  )
}

interface SearchResultsProps {
  response: SearchResponse | null
  loading: boolean
  error: string | null
}

export function SearchResults({ response, loading, error }: SearchResultsProps) {
  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 mb-12">
        <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      </div>
    )
  }

  if (!response && !loading) return null

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 mb-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white border border-gray-100 rounded-xl p-5 animate-pulse">
              <div className="h-4 bg-gray-100 rounded w-3/4 mb-3" />
              <div className="h-1.5 bg-gray-100 rounded w-full mb-3" />
              <div className="flex gap-2">
                <div className="h-5 bg-gray-100 rounded w-20" />
                <div className="h-5 bg-gray-100 rounded w-16" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!response || response.results.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 mb-12 text-center text-gray-400 text-sm">
        No results found.
      </div>
    )
  }

  return (
    <section className="max-w-4xl mx-auto px-4 mb-16">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">
          {response.total_results} results for <span className="font-medium text-gray-700">"{response.query}"</span>
        </p>
        {response.latency_ms > 0 && (
          <span className="text-xs font-mono text-gray-400">{response.latency_ms.toFixed(1)}ms</span>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {response.results.map(result => (
          <ResultCard key={result.product_id} result={result} />
        ))}
      </div>
    </section>
  )
}
