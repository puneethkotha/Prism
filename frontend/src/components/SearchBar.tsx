import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string) => void
  loading: boolean
}

const EXAMPLE_QUERIES = [
  'wireless noise cancelling headphones',
  'gaming laptop high performance',
  'smart home security camera',
  'portable USB-C charger',
  'mechanical keyboard RGB',
]

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('')

  const handleChange = (value: string) => {
    setQuery(value)
    onSearch(value)
  }

  return (
    <section className="px-4 mb-12">
      <div className="max-w-2xl mx-auto">
        <div className="relative">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            {loading
              ? <Loader2 className="w-5 h-5 text-prism-500 animate-spin" />
              : <Search className="w-5 h-5 text-gray-400" />
            }
          </div>
          <input
            type="text"
            value={query}
            onChange={e => handleChange(e.target.value)}
            placeholder="Search 25,000+ products by meaning..."
            className="w-full pl-12 pr-4 py-4 text-base border border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-prism-400 focus:border-transparent bg-white transition"
            autoFocus
          />
        </div>

        <div className="mt-3 flex flex-wrap gap-2 justify-center">
          {EXAMPLE_QUERIES.map(q => (
            <button
              key={q}
              onClick={() => handleChange(q)}
              className="text-xs text-gray-500 bg-gray-100 hover:bg-prism-50 hover:text-prism-700 border border-gray-200 hover:border-prism-200 rounded-full px-3 py-1 transition"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
