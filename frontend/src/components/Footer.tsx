export function Footer() {
  return (
    <footer className="border-t border-gray-100 py-8 px-4">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-400">
        <div>
          <span className="font-semibold text-gray-600">Prism</span>
          {' '}- AI Content Intelligence Platform
        </div>
        <div className="flex items-center gap-6">
          <a
            href="https://github.com/puneethkotha/Prism"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-gray-700 transition"
          >
            GitHub
          </a>
          <a href="#metrics" className="hover:text-gray-700 transition">
            Metrics
          </a>
          <span className="text-gray-300">Dataset: Amazon Reviews 2023</span>
        </div>
      </div>
    </footer>
  )
}
