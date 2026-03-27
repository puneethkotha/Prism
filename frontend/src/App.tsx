import { Hero } from './components/Hero'
import { SearchBar } from './components/SearchBar'
import { SearchResults } from './components/SearchResults'
import { MetricsDashboard } from './components/MetricsDashboard'
import { ArchitectureDiagram } from './components/ArchitectureDiagram'
import { Footer } from './components/Footer'
import { useSearch } from './hooks/useSearch'

export default function App() {
  const { results, loading, error, debouncedSearch } = useSearch()

  return (
    <div className="min-h-screen bg-white font-sans">
      <Hero />
      <SearchBar onSearch={debouncedSearch} loading={loading} />
      <SearchResults response={results} loading={loading} error={error} />
      <MetricsDashboard />
      <ArchitectureDiagram />
      <Footer />
    </div>
  )
}
