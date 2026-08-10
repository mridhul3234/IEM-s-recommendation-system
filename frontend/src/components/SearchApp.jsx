import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MagnifyingGlass, Globe } from '@phosphor-icons/react';
import ResultCard from './ResultCard';
import EqSliderGrid from './EqSliderGrid';

const INITIAL_TOP_K = 3;
const STEP_TOP_K = 3;

export default function SearchApp() {
  const DEFAULT_EXACT_FEATURES = {
    sub_bass: 0, bass: 0, low_mids: 0, mids: 0,
    presence: 0, treble: 0, air: 0,
    sibilance_risk: 0, tonal_tilt: 0, bass_to_treble: 0
  };

  const [query, setQuery] = useState('');
  const [advancedMode, setAdvancedMode] = useState(false);
  const [exactFeatures, setExactFeatures] = useState(DEFAULT_EXACT_FEATURES);
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
    if (!q && !advancedMode) return;

    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setResults([]);
    }
    setError(null);

    try {
      const ts = Date.now();
      let url = `http://localhost:8000/search?top_k=${targetTopK}&price_tier=${selectedPriceTier}&_t=${ts}`;
      if (advancedMode) {
        url += `&q=${encodeURIComponent(q || "")}&exact_features=${encodeURIComponent(JSON.stringify(exactFeatures))}`;
      } else {
        url += `&q=${encodeURIComponent(q)}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error('Search failed');
      const data = await res.json();
      
      setResults(data.results);
      setInferredFeatures(data.inferred_features);
      setCurrentTopK(targetTopK);

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
    if (query.trim() || advancedMode) {
      runSearch(query, INITIAL_TOP_K, false, tier);
    }
  };

  const handleFormSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim() && !advancedMode) return;
    runSearch(query, INITIAL_TOP_K, false, priceTier);
  };

  const handleSuggestMore = () => {
    const nextTopK = currentTopK + STEP_TOP_K;
    runSearch(query, nextTopK, true, priceTier);
  };

  const handleToggleCompare = (iemName) => {
    setCompareCart(prev => {
      if (prev.includes(iemName)) return prev.filter(n => n !== iemName);
      if (prev.length >= 3) return prev; 
      return [...prev, iemName];
    });
  };

  return (
    <div className="min-h-[100dvh] flex flex-col relative overflow-hidden bg-bgBase">
      
      {/* Navbar */}
      <nav className="flex items-center justify-between py-6 px-6 md:px-12 border-b border-white/5 relative z-30">
        <div className="flex items-center gap-2">
          <span className="font-display font-bold text-2xl tracking-tight text-textPrimary">Acoustic<span className="text-accentPrimary">Search.</span></span>
        </div>
        <div className="hidden md:flex items-center gap-10 text-sm font-medium text-textMuted">
          <a href="#" className="hover:text-textPrimary transition-colors flex items-center gap-1">Discover <span className="text-[9px]">▼</span></a>
          <a href="#" className="hover:text-textPrimary transition-colors">Support</a>
          <a href="#" className="hover:text-textPrimary transition-colors">About IEMs</a>
        </div>
        <div className="flex items-center gap-8">
          <button className="hidden md:flex items-center gap-2 text-sm text-textPrimary font-medium opacity-80 hover:opacity-100 transition-opacity">
            <Globe weight="bold" size={18} /> Language
          </button>
          <a 
            href={compareCart.length > 0 ? "/compare?" + compareCart.map((c, i) => `iem${i+1}=${encodeURIComponent(c)}`).join('&') : "#"}
            className="bg-accentPrimary text-bgBase px-6 py-2.5 rounded-full text-sm font-bold tracking-wide hover:brightness-110 transition-all shadow-[0_0_20px_rgba(255,138,76,0.3)] relative"
          >
            Compare {compareCart.length > 0 && `(${compareCart.length})`}
            {compareCart.length > 0 && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
              </span>
            )}
          </a>
        </div>
      </nav>

      {/* Hero Section Split Layout */}
      <div className="flex-1 flex flex-col relative z-10 w-full max-w-[1600px] mx-auto px-6 md:px-12 pt-12 md:pt-20 pb-48">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 h-full">
          {/* Left: Typography */}
          <div className="flex flex-col justify-center">
            <h1 className="font-display text-6xl md:text-8xl tracking-tighter leading-[0.95] text-textPrimary mb-6">
              <span className="font-light text-textMuted block mb-2">Discover</span>
              <span className="font-bold">Perfect Audio</span>
            </h1>
            <p className="font-body text-textMuted text-lg md:text-xl max-w-md leading-relaxed">
              Find and compare your exact acoustic target.
            </p>
          </div>
          
          {/* Right: Empty Area for IEM Photo */}
          <div className="hidden md:flex relative min-h-[400px] items-center justify-center">
             {/* Intentionally left blank for the IEM photo as requested */}
          </div>
        </div>
      </div>

      {/* Floating Glassmorphism Search Bar */}
      <div className="absolute bottom-10 left-6 right-6 md:left-12 md:right-12 z-40 max-w-[1500px] mx-auto">
        <div className="backdrop-blur-2xl bg-white/[0.03] border border-white/10 p-5 md:p-8 rounded-[2rem] shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)]">
          
          {/* Tabs */}
          <div className="flex items-center gap-2 mb-6">
            <button 
              onClick={() => handlePriceTierChange('all')}
              className={`px-5 py-2.5 rounded-full text-xs font-mono tracking-wider transition-all ${priceTier === 'all' ? 'bg-accentPrimary text-bgBase shadow-[0_0_15px_rgba(255,138,76,0.3)] font-bold' : 'bg-white/5 text-textPrimary hover:bg-white/10 border border-white/5'}`}
            >
              All Prices
            </button>
            <button 
              onClick={() => handlePriceTierChange('cheaper')}
              className={`px-5 py-2.5 rounded-full text-xs font-mono tracking-wider transition-all ${priceTier === 'cheaper' ? 'bg-accentPrimary text-bgBase shadow-[0_0_15px_rgba(255,138,76,0.3)] font-bold' : 'bg-white/5 text-textPrimary hover:bg-white/10 border border-white/5'}`}
            >
              Under $500
            </button>
            <button 
              onClick={() => handlePriceTierChange('costlier')}
              className={`px-5 py-2.5 rounded-full text-xs font-mono tracking-wider transition-all ${priceTier === 'costlier' ? 'bg-accentPrimary text-bgBase shadow-[0_0_15px_rgba(255,138,76,0.3)] font-bold' : 'bg-white/5 text-textPrimary hover:bg-white/10 border border-white/5'}`}
            >
              $500+
            </button>
          </div>

          {/* Inputs */}
          <form onSubmit={handleFormSubmit} className="flex flex-col md:flex-row gap-4 items-stretch md:items-center">
            
            {/* Target Query */}
            <div className="flex-1 bg-white/5 border border-white/10 rounded-[1.25rem] p-4 flex flex-col focus-within:border-accentPrimary/50 focus-within:bg-white/10 transition-colors">
              <label className="text-[10px] uppercase font-bold text-textMuted tracking-wider mb-1 ml-1">Target Sound</label>
              <input 
                type="text" 
                placeholder={advancedMode ? "Text search disabled in Advanced Mode" : "e.g. 'Very bassy but minimal treble'"}
                className="w-full bg-transparent text-textPrimary font-body font-medium text-lg outline-none placeholder-textPrimary/30 px-1 disabled:opacity-50"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={advancedMode}
              />
            </div>

            {/* Advanced EQ Toggle */}
            <button 
              type="button"
              onClick={() => setAdvancedMode(!advancedMode)}
              className={`text-left bg-white/5 border border-white/10 rounded-[1.25rem] p-4 flex flex-col min-w-[220px] transition-colors ${advancedMode ? 'border-accentPrimary/50 bg-accentPrimary/5' : 'hover:bg-white/10'}`}
            >
              <label className="text-[10px] uppercase font-bold text-textMuted tracking-wider mb-1 ml-1 cursor-pointer">Advanced EQ</label>
              <div className="text-textPrimary font-body font-medium text-lg px-1 mt-0.5">
                {advancedMode ? 'Active / Configured' : 'Configure Sliders'}
              </div>
            </button>

            {/* Submit Button */}
            <button 
              type="submit"
              disabled={loading}
              className="w-full md:w-[76px] h-[76px] shrink-0 bg-accentPrimary rounded-[1.25rem] flex items-center justify-center text-bgBase hover:brightness-110 active:scale-95 transition-all shadow-[0_0_20px_rgba(255,138,76,0.3)] disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="w-7 h-7 border-2 border-bgBase border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <MagnifyingGlass size={32} weight="bold" />
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Results & Advanced Mode Content (Appears below the fold) */}
      <AnimatePresence>
        {(advancedMode || results.length > 0 || error) && (
          <motion.div 
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="w-full bg-bgBase relative z-10 px-6 md:px-12 py-12 border-t border-white/5"
          >
            <div className="max-w-[1200px] mx-auto">
              
              {/* Advanced EQ Sliders */}
              {advancedMode && (
                <div className="mb-16">
                  <h2 className="font-mono text-sm text-accentPrimary uppercase tracking-widest mb-6">Advanced Acoustic Configuration</h2>
                  <EqSliderGrid 
                    exactFeatures={exactFeatures} 
                    setExactFeatures={setExactFeatures} 
                    runSearch={runSearch} 
                    loading={loading} 
                    query={query} 
                  />
                </div>
              )}

              {error && <div className="text-red-400 font-mono mb-8 p-4 bg-red-500/10 rounded-xl border border-red-500/20">{error}</div>}

              {/* Results */}
              {results.length > 0 && (
                <div className="space-y-16">
                  
                  {results.filter(r => r.features?.price < 500).length > 0 && (
                    <div>
                      <h3 className="font-display text-2xl font-light text-textPrimary tracking-wide mb-8 border-b border-white/10 pb-4">
                        Cheaper Picks <span className="text-textMuted text-lg ml-2 font-body">Under $500</span>
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                      <h3 className="font-display text-2xl font-light text-textPrimary tracking-wide mb-8 border-b border-white/10 pb-4">
                        Costlier Picks <span className="text-textMuted text-lg ml-2 font-body">$500+</span>
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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

                  {hasMore ? (
                    <div className="flex justify-center mt-12">
                      <button
                        type="button"
                        onClick={handleSuggestMore}
                        disabled={loadingMore}
                        className="px-8 py-4 bg-white/5 border border-white/10 hover:border-accentPrimary hover:bg-accentPrimary/5 text-textPrimary hover:text-accentPrimary font-mono uppercase tracking-wider text-xs rounded-xl transition-all duration-300 disabled:opacity-50"
                      >
                        {loadingMore ? 'Loading...' : 'Load More IEMs'}
                      </button>
                    </div>
                  ) : (
                    <div className="text-center font-mono text-xs text-textMuted uppercase tracking-widest mt-12 opacity-50">
                      End of Recommendations
                    </div>
                  )}
                  
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

