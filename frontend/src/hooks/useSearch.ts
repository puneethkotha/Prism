import { useState, useCallback, useRef } from 'react'
import { search } from '../lib/api'
import type { SearchResponse } from '../types'

export function useSearch() {
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const runSearch = useCallback(async (query: string, k = 10) => {
    if (!query.trim() || query.trim().length < 2) {
      setResults(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await search(query, k)
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const debouncedSearch = useCallback((query: string, delay = 350) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => runSearch(query), delay)
  }, [runSearch])

  return { results, loading, error, runSearch, debouncedSearch }
}
