import React, { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [rankFilter, setRankFilter] = useState('all');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  const [docTypeFilter, setDocTypeFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [searchHistory, setSearchHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('searchHistory') || '[]');
    } catch {
      return [];
    }
  });

  const fetchSuggestions = async (val) => {
    if (!val || val.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    try {
      const resp = await fetch(`http://localhost:8000/suggest?q=${encodeURIComponent(val)}`);
      if (!resp.ok) throw new Error("API error");
      const data = await resp.json();
      if (data && data.suggestions) {
        setSuggestions(data.suggestions);
        setShowSuggestions(true);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch {
      // fallback: show previous queries or static
      setSuggestions([val + " example", val + " test"]);
      setShowSuggestions(true);
    }
  };

  const handleInputChange = (e) => {
    setQuery(e.target.value);
    setSelectedSuggestion(-1);
    fetchSuggestions(e.target.value);
  };

  const handleSuggestionClick = (s) => {
    setQuery(s);
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
  };

  const handleInputKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      setSelectedSuggestion((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      setSelectedSuggestion((prev) => Math.max(prev - 1, 0));
    } else if (e.key === "Enter" && selectedSuggestion >= 0) {
      setQuery(suggestions[selectedSuggestion]);
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    }
  };

  const handleHistoryClick = (term) => {
    setQuery(term);
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
    setTimeout(() => {
      document.getElementById('search-input')?.focus();
    }, 0);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResults([]);
    setSearched(false);
    try {
      // Save search history (max 5)
      setSearchHistory(prev => {
        const updated = [query, ...prev.filter(t => t !== query)].slice(0, 5);
        localStorage.setItem('searchHistory', JSON.stringify(updated));
        return updated;
      });
      const resp = await fetch(
        `http://localhost:8000/search?q=${encodeURIComponent(query)}&limit=10&offset=0`
      );
      if (!resp.ok) throw new Error("API error");
      const data = await resp.json();
      if (data && data.results) {
        setResults(
          data.results.map((r, i) => ({
            title: r.title,
            snippet: r.snippet,
            url: "#", // Could link to full doc if available
            rank: i + 1,
            score: r.score,
            docType: i % 2 === 0 ? 'report' : 'note', // mock
            date: `2024-0${(i%3)+1}-0${(i%7)+1}` // mock
          }))
        );
      } else {
        setResults([]);
      }
      setSearched(true);
    } catch (err) {
      setError("An error occurred while searching.");
      setResults([]);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  };

  // Helper to highlight query terms in snippet
  function highlightSnippet(snippet, query) {
    if (!query) return snippet;
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return snippet.split(re).map((part, i) =>
      re.test(part) ? <b key={i} className="bg-yellow-200 font-semibold">{part}</b> : part
    );
  }

  // Filtered results
  let filteredResults = results;
  if (rankFilter !== 'all') filteredResults = filteredResults.filter(res => String(res.rank) === rankFilter);
  if (docTypeFilter !== 'all') filteredResults = filteredResults.filter(res => res.docType === docTypeFilter);
  if (dateFilter !== 'all') filteredResults = filteredResults.filter(res => res.date === dateFilter);

  // Dark mode state
  const [darkMode, setDarkMode] = useState(() => {
    try {
      return localStorage.getItem('darkMode') === 'true';
    } catch {
      return false;
    }
  });
  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  return (
    <div className={`min-h-screen flex flex-col items-center px-4 transition-colors duration-300 ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <header className="w-full max-w-xl py-8 text-center" role="banner">
        <div className="flex flex-col items-center gap-2">
          <img src="logo.svg" alt="Logo" className="h-12 w-12 mb-2" aria-hidden="true" />
          <h1 className="text-3xl font-bold mb-2 font-sans">Search Algorithm Engine</h1>
        </div>
        <p className={`font-sans ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Search documents locally with fast and accurate results.</p>
        <button
          className={`absolute right-4 top-4 px-3 py-1 rounded transition-colors duration-200 text-xs font-semibold ${darkMode ? 'bg-gray-700 text-yellow-200 hover:bg-gray-600' : 'bg-yellow-200 text-gray-800 hover:bg-yellow-300'}`}
          onClick={() => setDarkMode(v => !v)}
          aria-label="Toggle dark mode"
        >
          {darkMode ? '☀️ Light' : '🌙 Dark'}
        </button>
      </header>
      <main className="w-full max-w-xl flex flex-col items-center">
        <form onSubmit={handleSearch} className="w-full flex mb-6 relative" role="search" aria-label="Search form">
          <label htmlFor="search-input" className="sr-only">Search query</label>
          <input
            id="search-input"
            type="text"
            className="flex-grow px-4 py-2 rounded-l-md border border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-600 font-sans text-gray-900"
            placeholder="Enter search terms..."
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleInputKeyDown}
            aria-label="Search query"
            autoFocus
          />
          {showSuggestions && suggestions.length > 0 && (
            <ul className="absolute z-10 left-0 right-0 mt-12 bg-white border border-gray-200 rounded shadow-lg max-h-48 overflow-y-auto" role="listbox">
              {suggestions.map((s, i) => (
                <li
                  key={s}
                  className={`px-4 py-2 cursor-pointer ${i === selectedSuggestion ? 'bg-blue-100' : ''}`}
                  onMouseDown={() => handleSuggestionClick(s)}
                  role="option"
                  aria-selected={i === selectedSuggestion}
                >
                  {s}
                </li>
              ))}
            </ul>
          )}
          <button
            type="submit"
            className="px-6 py-2 bg-blue-700 text-white font-semibold rounded-r-md hover:bg-blue-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-600 font-sans"
            disabled={loading || !query.trim()}
            tabIndex={0}
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
        {searchHistory.length > 0 && (
          <div className="w-full flex flex-wrap gap-2 mb-2">
            {searchHistory.map((term, i) => (
              <button
                key={term}
                type="button"
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-xs hover:bg-blue-100 hover:text-blue-700 transition-colors"
                onClick={() => handleHistoryClick(term)}
                tabIndex={0}
              >
                {term}
              </button>
            ))}
          </div>
        )}
        <section className="w-full">
          {loading && (
            <div className="flex justify-center py-8">
              <div className="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-10 w-10"></div>
            </div>
          )}
          {error && (
            <div className="text-red-600 text-center mb-4">{error}</div>
          )}
          {searched && !loading && results.length === 0 && (
            <div className="text-gray-500 text-center">No results found.</div>
          )}
          {results.length > 0 && (
            <>
              <div className="mb-4 flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <label htmlFor="rankFilter" className="text-sm text-gray-600">Rank:</label>
                  <select
                    id="rankFilter"
                    className="border rounded px-2 py-1"
                    value={rankFilter}
                    onChange={e => setRankFilter(e.target.value)}
                  >
                    <option value="all">All</option>
                    {[...new Set(results.map(r => r.rank))].map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <label htmlFor="docTypeFilter" className="text-sm text-gray-600">Type:</label>
                  <select
                    id="docTypeFilter"
                    className="border rounded px-2 py-1"
                    value={docTypeFilter}
                    onChange={e => setDocTypeFilter(e.target.value)}
                  >
                    <option value="all">All</option>
                    {[...new Set(results.map(r => r.docType))].map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <label htmlFor="dateFilter" className="text-sm text-gray-600">Date:</label>
                  <select
                    id="dateFilter"
                    className="border rounded px-2 py-1"
                    value={dateFilter}
                    onChange={e => setDateFilter(e.target.value)}
                  >
                    <option value="all">All</option>
                    {[...new Set(results.map(r => r.date))].map(d => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
              </div>
              <ul className="space-y-4" role="list">
                {filteredResults.map((res, idx) => (
                  <li
                    key={idx}
                    className={`p-4 rounded shadow flex flex-col gap-1 transition-all duration-500 animate-fadein ${darkMode ? 'bg-gray-800 text-gray-100' : 'bg-white'}`}
                    tabIndex={0}
                    aria-label={`Result ${idx + 1}: ${res.title}`}
                    style={{animationDelay: `${idx * 60}ms`}}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>#{res.rank}</span>
                      <a
                        href={res.url}
                        className={`font-semibold focus:outline-none focus:ring-2 font-sans transition-colors duration-150 ${darkMode ? 'text-blue-300 hover:underline focus:ring-blue-400' : 'text-blue-800 hover:underline focus:ring-blue-600'}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {res.title}
                      </a>
                      <span className={`ml-auto text-xs font-mono ${darkMode ? 'text-green-400' : 'text-green-700'}`}>Score: {typeof res.score === 'number' ? res.score.toFixed(3) : '-'}</span>
                    </div>
                    <div className={`font-sans ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>{highlightSnippet(res.snippet, query)}</div>
                  </li>
                ))}
              </ul>
              <style>{`
                @keyframes fadein { from { opacity: 0; transform: translateY(10px);} to { opacity: 1; transform: none; } }
                .animate-fadein { animation: fadein 0.6s both; }
              `}</style>
            </>
          )}
        </section>
      </main>
      <footer className="w-full max-w-xl py-6 mt-auto text-center text-gray-400 text-sm">
        &copy; {new Date().getFullYear()} Search Algorithm Engine
      </footer>
      <style>{`
        .loader {
          border-top-color: #3498db;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default App;
