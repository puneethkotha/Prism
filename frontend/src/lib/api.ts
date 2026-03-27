import type { SearchResponse, EvaluationMetrics, DemoResults } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''
const IS_STATIC = !API_BASE

let demoCache: DemoResults | null = null

async function loadDemoData(): Promise<DemoResults> {
  if (demoCache) return demoCache
  const res = await fetch(`${import.meta.env.BASE_URL}demo_results.json`)
  if (!res.ok) throw new Error('Failed to load demo data')
  demoCache = await res.json()
  return demoCache!
}

function closestDemoQuery(query: string, demos: DemoResults): string {
  const q = query.toLowerCase()
  const keys = Object.keys(demos)
  // Exact match first
  const exact = keys.find(k => k.toLowerCase() === q)
  if (exact) return exact
  // Score by word overlap
  const queryWords = q.split(/\s+/).filter(Boolean)
  let best = keys[0]
  let bestScore = 0
  for (const key of keys) {
    const keyWords = key.toLowerCase().split(/\s+/)
    const overlap = queryWords.filter(w => keyWords.some(k => k.includes(w) || w.includes(k))).length
    if (overlap > bestScore) {
      bestScore = overlap
      best = key
    }
  }
  return best
}

export async function search(query: string, k = 10): Promise<SearchResponse> {
  if (IS_STATIC) {
    const demos = await loadDemoData()
    const matchedQuery = closestDemoQuery(query, demos)
    const results = (demos[matchedQuery] ?? []).slice(0, k)
    return {
      query,
      results,
      latency_ms: 0,
      total_results: results.length,
    }
  }

  const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&k=${k}`)
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`)
  return res.json()
}

export async function getMetrics(): Promise<EvaluationMetrics> {
  if (IS_STATIC) {
    const res = await fetch(`${import.meta.env.BASE_URL}metrics.json`)
    if (!res.ok) throw new Error('Metrics not available')
    return res.json()
  }

  const res = await fetch(`${API_BASE}/metrics`)
  if (!res.ok) throw new Error(`Metrics failed: ${res.statusText}`)
  return res.json()
}

export async function extractTags(text: string): Promise<{ tags: Record<string, unknown>; latency_ms: number }> {
  if (IS_STATIC) throw new Error('Live extraction requires the backend API')
  const res = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(`Extraction failed: ${res.statusText}`)
  return res.json()
}
