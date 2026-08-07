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
  const [priceTier, setPriceTier] = useState('all'); // 'all', 'cheaper', 'costlier'
  const [results, setResults] = useState([]);
  const [inferredFeatures, setInferredFeatures] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentTopK, setCurrentTopK] = useState(INITIAL_TOP_K);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const [compareCart, setCompareCart] = useState([]);

  const runSearch = async (searchQuery, targetTopK = INITIAL_TOP_K, isLoadMore = false, selectedPriceTier = priceTier) => {
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
      const res = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(q)}&top_k=${targetTopK}&price_tier=${selectedPriceTier}&_t=${ts}`);
      if (!res.ok) throw new Error('Search failed');
      const data = await res.json();
      
      setResults(data.results);
      setInferredFeatures(data.inferred_features);
      setCurrentTopK(targetTopK);

      // If returned results are fewer than requested, we've reached the dataset limit
      if (data.results.length < targetTopK) {
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

  const handlePriceTierChange = (tier) => {
    setPriceTier(tier);
    if (query.trim()) {
      runSearch(query, INITIAL_TOP_K, false, tier);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    runSearch(query, INITIAL_TOP_K, false, priceTier);
  };

  const handleChipClick = (featureText) => {
    setQuery(featureText);
    runSearch(featureText, INITIAL_TOP_K, false, priceTier);
  };

  const handleSuggestMore = () => {
    const nextTopK = currentTopK + STEP_TOP_K;
    runSearch(query, nextTopK, true, priceTier);
  };

  const handleToggleCompare = (iemName) => {
    setCompareCart(prev => {
      if (prev.includes(iemName)) return prev.filter(n => n !== iemName);
      if (prev.length >= 3) return prev; // Max 3 items
      return [...prev, iemName];
    });
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

      {/* Price Tier Selection Buttons */}
      <div className="flex justify-center gap-3 mb-6">
        <button
          type="button"
          onClick={() => handlePriceTierChange('all')}
          className={`px-4 py-2 font-mono text-xs uppercase tracking-wider rounded-lg border transition-all duration-200 ${
            priceTier === 'all'
              ? 'bg-accentPrimary text-bgSurface font-bold border-accentPrimary shadow-lg'
              : 'bg-bgSurface text-textMuted border-bgBorder hover:border-accentPrimary/50 hover:text-textPrimary'
          }`}
        >
          All Prices
        </button>
        <button
          type="button"
          onClick={() => handlePriceTierChange('cheaper')}
          className={`px-4 py-2 font-mono text-xs uppercase tracking-wider rounded-lg border transition-all duration-200 ${
            priceTier === 'cheaper'
              ? 'bg-accentPrimary text-bgSurface font-bold border-accentPrimary shadow-lg'
              : 'bg-bgSurface text-textMuted border-bgBorder hover:border-accentPrimary/50 hover:text-textPrimary'
          }`}
        >
          Cheaper (&lt; $500)
        </button>
        <button
          type="button"
          onClick={() => handlePriceTierChange('costlier')}
          className={`px-4 py-2 font-mono text-xs uppercase tracking-wider rounded-lg border transition-all duration-200 ${
            priceTier === 'costlier'
              ? 'bg-accentPrimary text-bgSurface font-bold border-accentPrimary shadow-lg'
              : 'bg-bgSurface text-textMuted border-bgBorder hover:border-accentPrimary/50 hover:text-textPrimary'
          }`}
        >
          Costlier (&ge; $500)
        </button>
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
        
        {results.filter(r => r.features?.price < 500).length > 0 && (
          <div>
            <h3 className="font-display text-xl text-textPrimary tracking-wide uppercase mb-6 border-b border-bgBorder pb-2">
              Cheaper Picks (Under $500)
            </h3>
            <div className="space-y-8">
              {results.filter(r => r.features?.price < 500).map((res) => (
                <ResultCard 
                  key={res.name} 
                  result={res} 
                  rank={results.indexOf(res) + 1} 
                  isCompared={compareCart.includes(res.name)}
                  onToggleCompare={() => handleToggleCompare(res.name)}
                />
              ))}
            </div>
          </div>
        )}

        {results.filter(r => !r.features?.price || r.features?.price >= 500).length > 0 && (
          <div>
            <h3 className="font-display text-xl text-textPrimary tracking-wide uppercase mb-6 border-b border-bgBorder pb-2">
              Costlier Picks ($500+)
            </h3>
            <div className="space-y-8">
              {results.filter(r => !r.features?.price || r.features?.price >= 500).map((res) => (
                <ResultCard 
                  key={res.name} 
                  result={res} 
                  rank={results.indexOf(res) + 1}
                  isCompared={compareCart.includes(res.name)}
                  onToggleCompare={() => handleToggleCompare(res.name)}
                />
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

      {/* Floating Compare Action Bar */}
      {compareCart.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-[#080b10] border border-accentPrimary/50 shadow-2xl shadow-accentPrimary/20 rounded-full px-6 py-3 flex items-center gap-6 z-50">
          <span className="font-mono text-xs text-textPrimary uppercase tracking-widest">
            {compareCart.length} selected
          </span>
          <a 
            href={"/compare?" + compareCart.map((c, i) => `iem${i+1}=${encodeURIComponent(c)}`).join('&')}
            className="px-4 py-2 bg-accentPrimary text-bgSurface rounded-full font-mono text-xs uppercase tracking-wider font-bold hover:opacity-90 transition-opacity"
          >
            Compare Now
          </a>
        </div>
      )}
    </div>
  );
}
