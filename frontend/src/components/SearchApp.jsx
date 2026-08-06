import React, { useState } from 'react';
import ResultCard from './ResultCard';

const SUGGESTED_FEATURES = [
  'Very bassy',
  'Warm & punchy',
  'Sub-bass rumble',
  'Bright & airy',
  'Smooth vocals',
  'Balanced neutral',
  'V-shaped fun'
];

export default function SearchApp() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [inferredFeatures, setInferredFeatures] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runSearch = async (searchQuery) => {
    const q = searchQuery.trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const res = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(q)}&top_k=6`);
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

  const handleFormSubmit = (e) => {
    e.preventDefault();
    runSearch(query);
  };

  const handleChipClick = (featureText) => {
    setQuery(featureText);
    runSearch(featureText);
  };

  return (
    <div className="max-w-4xl mx-auto mt-12 px-4 pb-16">
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
      <form onSubmit={handleFormSubmit} className="relative group max-w-2xl mx-auto mb-6">
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

      {/* Quick Search Feature Suggestions */}
      <div className="max-w-2xl mx-auto mb-12">
        <div className="text-xs font-mono text-textMuted uppercase tracking-widest mb-3 text-center">
          Suggested Acoustic Traits:
        </div>
        <div className="flex flex-wrap gap-2 justify-center">
          {SUGGESTED_FEATURES.map((feature, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleChipClick(feature)}
              className="px-3 py-1.5 bg-bgSurface border border-bgBorder hover:border-accentPrimary/50 text-textMuted hover:text-accentPrimary rounded-full font-mono text-xs transition-colors duration-200"
            >
              + {feature}
            </button>
          ))}
        </div>
      </div>

      {/* Results Header */}
      {results.length > 0 && (
        <div className="flex justify-between items-center mb-6 border-b border-bgBorder pb-3">
          <span className="font-mono text-xs text-textMuted uppercase tracking-widest">
            Found {results.length} Matching IEMs
          </span>
          <span className="font-mono text-xs text-accentPrimary">
            Top Recommendations
          </span>
        </div>
      )}

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
