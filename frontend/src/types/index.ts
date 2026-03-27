export interface ExtractedTags {
  category: string
  subcategory: string
  key_features: string[]
  use_case: string
  target_audience: string
  complexity: 'Beginner' | 'Intermediate' | 'Advanced'
  sentiment: 'Positive' | 'Neutral' | 'Negative'
}

export interface SearchResult {
  product_id: number
  asin: string
  title: string
  tags: ExtractedTags
  similarity_score: number
  rank: number
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  latency_ms: number
  total_results: number
}

export interface EvaluationMetrics {
  precision: number
  recall: number
  f1: number
  avg_latency_ms: number
  p50_latency_ms: number
  p95_latency_ms: number
  p99_latency_ms: number
  total_products: number
  tagged_products: number
  tagging_reduction_pct: number
  sample_size: number
}

export type DemoResults = Record<string, SearchResult[]>
