import React, { useState } from 'react';
import ResultCard from './ResultCard';

export default function SearchApp() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [inferredFeatures, setInferredFeatures] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setResults([]);
    
    try {
      // Hit the Python FastAPI server
      const res = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error('Search failed');
      const data = await res.json();
      setResults(data.results);
      setInferredFeatures(data.inferred_features);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-12 px-4">
      {/* Search Header */}
      <div className="text-center mb-12">
        <h1 className="font-display text-4xl font-light text-textPrimary tracking-wide uppercase mb-4">
          Acoustic<span className="text-accentPrimary font-bold">Search</span>
        </h1>
        <p className="font-body text-textMuted max-w-xl mx-auto">
          Describe the exact tonal properties you are looking for in an IEM. Our hybrid engine will extract your acoustic target and find the closest matches.
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="relative group max-w-2xl mx-auto mb-16">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-accentSecondary to-accentPrimary rounded-lg blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
        <div className="relative flex items-center bg-bgSurface border border-bgBorder rounded-lg overflow-hidden">
          <input 
            type="text" 
            className="w-full bg-transparent text-textPrimary font-body px-6 py-4 outline-none placeholder-textMuted/50"
            placeholder="e.g. 'Very bassy but minimal treble'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button 
            type="submit"
            disabled={loading}
            className="px-6 py-4 text-accentPrimary font-mono uppercase tracking-wider hover:bg-accentPrimary/10 transition-colors disabled:opacity-50"
          >
            {loading ? 'Scanning...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Results */}
      <div className="space-y-8">
        {error && <div className="text-red-400 font-mono text-center">{error}</div>}
        
        {results.map((res, i) => (
          <ResultCard key={i} result={res} rank={i + 1} />
        ))}
      </div>
    </div>
  );
}
