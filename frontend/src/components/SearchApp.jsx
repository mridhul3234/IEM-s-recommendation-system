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

const INITIAL_TOP_K = 3;
const STEP_TOP_K = 3;

export default function SearchApp() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [inferredFeatures, setInferredFeatures] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentTopK, setCurrentTopK] = useState(INITIAL_TOP_K);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);

  const runSearch = async (searchQuery, targetTopK = INITIAL_TOP_K, isLoadMore = false) => {
    const q = searchQuery.trim();
    if (!q) return;

    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setResults([]);
    }
    setError(null);

    try {
      const ts = Date.now();
      const res = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(q)}&top_k=${targetTopK}&_t=${ts}`);
      if (!res.ok) throw new Error('Search failed');
      const data = await res.json();
      
      setResults(data.results);
      setInferredFeatures(data.inferred_features);
      setCurrentTopK(targetTopK);

      // If returned results are fewer than requested, we've reached the dataset limit
      if (data.results.length < targetTopK || data.results.length >= 8) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    runSearch(query, INITIAL_TOP_K, false);
  };

  const handleChipClick = (featureText) => {
    setQuery(featureText);
    runSearch(featureText, INITIAL_TOP_K, false);
  };

  const handleSuggestMore = () => {
    const nextTopK = currentTopK + STEP_TOP_K;
    runSearch(query, nextTopK, true);
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

      {/* Results List */}
      <div className="space-y-12">
        {error && <div className="text-red-400 font-mono text-center">{error}</div>}
        
        {results.filter(r => r.features?.price < 200).length > 0 && (
          <div>
            <h3 className="font-display text-xl text-textPrimary tracking-wide uppercase mb-6 border-b border-bgBorder pb-2">
              Budget Picks (Under $200)
            </h3>
            <div className="space-y-8">
              {results.filter(r => r.features?.price < 200).map((res) => (
                <ResultCard key={res.name} result={res} rank={results.indexOf(res) + 1} />
              ))}
            </div>
          </div>
        )}

        {results.filter(r => !r.features?.price || r.features?.price >= 200).length > 0 && (
          <div>
            <h3 className="font-display text-xl text-textPrimary tracking-wide uppercase mb-6 border-b border-bgBorder pb-2">
              Premium Picks ($200+)
            </h3>
            <div className="space-y-8">
              {results.filter(r => !r.features?.price || r.features?.price >= 200).map((res) => (
                <ResultCard key={res.name} result={res} rank={results.indexOf(res) + 1} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 'Suggest More' Button */}
      {results.length > 0 && (
        <div className="text-center mt-10">
          {hasMore ? (
            <button
              type="button"
              onClick={handleSuggestMore}
              disabled={loadingMore}
              className="px-8 py-3.5 bg-bgSurface border border-accentPrimary/40 hover:border-accentPrimary text-accentPrimary font-mono uppercase tracking-wider text-xs rounded-lg hover:bg-accentPrimary/10 transition-all duration-300 shadow-lg disabled:opacity-50"
            >
              {loadingMore ? 'Loading More IEMs...' : 'Suggest More'}
            </button>
          ) : (
            <div className="font-mono text-xs text-textMuted uppercase tracking-widest border-t border-bgBorder pt-6">
              All top matching IEMs loaded
            </div>
          )}
        </div>
      )}
    </div>
  );
}
