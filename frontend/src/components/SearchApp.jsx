import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MagnifyingGlass, Globe, Cpu, Target, Waves, CaretDown, ArrowsLeftRight, WarningCircle, SlidersHorizontal } from '@phosphor-icons/react';
import ResultCard from './ResultCard';
import EqSliderGrid from './EqSliderGrid';
import ScrollFrameBackground from './ScrollFrameBackground';

const INITIAL_TOP_K = 3;
const STEP_TOP_K = 3;

const FAQ_ITEMS = [
  {
    q: "What makes AcousticSearch different from regular headphone recommendation sites?",
    a: "Unlike static buyer's guides or generic review aggregators, AcousticSearch utilizes AI natural language processing (Google Gemini) and vector similarity math over actual measured frequency response (FR) curves. It extracts your target tonal preferences and matches them mathematically against physical IEM acoustic profiles."
  },
  {
    q: "What is the difference between Semantic NLP Match and Acoustic Math Match?",
    a: "Semantic NLP measures how closely an IEM's sound signature description matches the text query you typed. Acoustic Math calculates the exact Euclidean distance between your desired acoustic target values (sub-bass, presence, air, etc.) and the IEM's measured frequency response properties."
  },
  {
    q: "How does the Advanced Acoustic EQ sliders work?",
    a: "Advanced EQ gives you direct 10-band slider control over sub-bass, bass, presence, treble, air, tonal tilt, and sibilance risk. You can manually configure your exact target sound signature and query the database directly."
  },
  {
    q: "Is the frequency response data accurate?",
    a: "Yes. All IEM acoustic properties in our database are computed directly from standardized 711 coupler frequency response measurements and normalized acoustic metrics. No data is fabricated."
  },
  {
    q: "How does the IEM comparison feature work?",
    a: "Click the '+ Compare' button on any recommendation card to add up to 3 IEMs to your comparison drawer. Click 'Compare' in the top right or the bottom floating drawer to compare their sound signatures, prices, and acoustic trait distributions side-by-side."
  }
];

function FaqAccordionItem({ question, answer }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-white/10 rounded-2xl bg-white/[0.03] backdrop-blur-xl overflow-hidden transition-colors hover:border-white/20">
      <motion.button 
        whileTap={{ scale: 0.99 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-6 text-left flex items-center justify-between gap-4 font-display font-semibold text-lg text-textPrimary cursor-pointer select-none"
      >
        <span>{question}</span>
        <div className={`p-2 rounded-full bg-white/5 text-accentPrimary transition-transform duration-300 ${isOpen ? 'rotate-180 bg-accentPrimary/20' : ''}`}>
          <CaretDown size={18} weight="bold" />
        </div>
      </motion.button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="px-6 pb-6 pt-2 font-body text-textMuted text-base leading-relaxed border-t border-white/5">
              {answer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function SearchApp() {
  const DEFAULT_EXACT_FEATURES = {
    sub_bass: 0, bass: 0, low_mids: 0, mids: 0,
    presence: 0, treble: 0, air: 0,
    sibilance_risk: 0, tonal_tilt: 0, bass_to_treble: 0
  };

  const [query, setQuery] = useState('');
  const [exactFeatures, setExactFeatures] = useState(DEFAULT_EXACT_FEATURES);
  const [priceTier, setPriceTier] = useState('all'); 
  const [results, setResults] = useState([]);
  const [inferredFeatures, setInferredFeatures] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentTopK, setCurrentTopK] = useState(INITIAL_TOP_K);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const [compareCart, setCompareCart] = useState([]);
  const [compareNotice, setCompareNotice] = useState(null);

  const runSearch = async (searchQuery, targetTopK = INITIAL_TOP_K, isLoadMore = false, selectedPriceTier = priceTier, isEqMode = false) => {
    const q = searchQuery.trim();
    if (!q && !isEqMode) return;

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
      if (isEqMode) {
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
    if (query.trim()) {
      runSearch(query, INITIAL_TOP_K, false, tier);
    }
  };

  const handleFormSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    runSearch(query, INITIAL_TOP_K, false, priceTier);
  };

  const handleSuggestMore = () => {
    const nextTopK = currentTopK + STEP_TOP_K;
    runSearch(query, nextTopK, true, priceTier);
  };

  const handleToggleCompare = (iemName) => {
    setCompareNotice(null);
    setCompareCart(prev => {
      if (prev.includes(iemName)) return prev.filter(n => n !== iemName);
      if (prev.length >= 3) return prev; 
      return [...prev, iemName];
    });
  };

  const handleNavCompareClick = (e) => {
    if (compareCart.length < 2) {
      e.preventDefault();
      setCompareNotice("Select at least 2 IEMs to compare side-by-side.");
      setTimeout(() => setCompareNotice(null), 4000);
    } else {
      window.location.href = "/compare?" + compareCart.map((c, i) => `iem${i+1}=${encodeURIComponent(c)}`).join('&');
    }
  };

  const scrollToAdvancedEq = () => {
    document.getElementById('advanced-eq')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-[100dvh] flex flex-col bg-bgBase text-textPrimary selection:bg-accentPrimary/30 selection:text-accentPrimary relative">
      
      {/* Dynamic 180-Frame Scroll Background */}
      <ScrollFrameBackground />

      {/* Transparent Sticky Navbar */}
      <nav className="sticky top-0 flex items-center justify-between py-5 px-6 md:px-12 bg-transparent z-50 pointer-events-auto">
        
        {/* Brand Name Only */}
        <div className="flex items-center">
          <a href="/" className="font-display font-bold text-2xl tracking-tight text-textPrimary hover:opacity-90 transition-opacity">
            Acoustic<span className="text-accentPrimary">Search.</span>
          </a>
        </div>
        
        {/* Centered Glassmorphism Floating Pill Container - Low opacity glass */}
        <div className="hidden md:flex items-center gap-1 bg-[#0F141C]/60 backdrop-blur-2xl border border-white/10 rounded-full px-3 py-1.5 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <a href="/#how-it-works" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider text-textMuted hover:text-textPrimary hover:bg-white/10 transition-all">
            How It Works
          </a>
          <a href="#advanced-eq" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider text-textMuted hover:text-textPrimary hover:bg-white/10 transition-all">
            Advanced EQ
          </a>
          <a href="#faq" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider text-textMuted hover:text-textPrimary hover:bg-white/10 transition-all">
            FAQ
          </a>
          <a href="/about" className="px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider text-textMuted hover:text-textPrimary hover:bg-white/10 transition-all">
            About IEMs
          </a>
        </div>

        {/* Right CTA Button */}
        <div className="flex items-center gap-4">
          <button className="hidden lg:flex items-center gap-2 text-xs font-mono uppercase text-textMuted hover:text-textPrimary transition-colors">
            <Globe weight="bold" size={16} /> EN
          </button>
          
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleNavCompareClick}
            className="bg-accentPrimary text-black px-6 py-2.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider hover:brightness-110 transition-all shadow-[0_0_20px_rgba(210,248,91,0.35)] relative cursor-pointer flex items-center gap-2"
          >
            <ArrowsLeftRight size={16} weight="bold" />
            Compare {compareCart.length > 0 && `(${compareCart.length})`}
            {compareCart.length > 0 && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-black opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-black"></span>
              </span>
            )}
          </motion.button>
        </div>
      </nav>

      {/* Compare Notice Toast */}
      <AnimatePresence>
        {compareNotice && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-accentPrimary text-black font-mono text-xs uppercase tracking-wider px-6 py-3 rounded-full shadow-2xl flex items-center gap-2 border border-black/20 font-bold"
          >
            <WarningCircle size={18} weight="bold" />
            {compareNotice}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Fullscreen Hero Section */}
      <div className="relative z-20 w-full min-h-[calc(100vh-80px)] flex flex-col justify-between pt-12 md:pt-20 pb-16 overflow-hidden">
        
        {/* Hero Content - Fully Transparent without card box */}
        <div className="relative z-10 w-full max-w-[1600px] mx-auto px-6 md:px-12 my-auto">
          <div className="max-w-2xl">
            <h1 className="font-display text-6xl md:text-8xl tracking-tighter leading-[0.95] text-textPrimary mb-6 drop-shadow-2xl">
              <span className="font-light text-textMuted block mb-2">Discover</span>
              <span className="font-bold">Perfect Audio</span>
            </h1>
            <p className="font-body text-textMuted text-lg md:text-xl max-w-md leading-relaxed drop-shadow-lg">
              Find and compare your exact acoustic target.
            </p>
          </div>
        </div>

        {/* Integrated Glassmorphism Search Bar - Translucent */}
        <div className="relative z-30 max-w-[1500px] w-full mx-auto px-6 md:px-12 mt-12">
          <div className="backdrop-blur-2xl bg-[#0F141C]/50 border border-white/10 p-5 md:p-8 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.6)]">
            
            {/* Tabs */}
            <div className="flex items-center gap-2 mb-6">
              <motion.button 
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handlePriceTierChange('all')}
                className={`px-5 py-2.5 rounded-full text-xs font-mono tracking-wider transition-all cursor-pointer ${priceTier === 'all' ? 'bg-accentPrimary text-black shadow-[0_0_15px_rgba(210,248,91,0.4)] font-bold' : 'bg-white/5 text-textPrimary hover:bg-white/10 border border-white/5'}`}
              >
                All Prices
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handlePriceTierChange('cheaper')}
                className={`px-5 py-2.5 rounded-full text-xs font-mono tracking-wider transition-all cursor-pointer ${priceTier === 'cheaper' ? 'bg-accentPrimary text-black shadow-[0_0_15px_rgba(210,248,91,0.4)] font-bold' : 'bg-white/5 text-textPrimary hover:bg-white/10 border border-white/5'}`}
              >
                Under $500
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handlePriceTierChange('costlier')}
                className={`px-5 py-2.5 rounded-full text-xs font-mono tracking-wider transition-all cursor-pointer ${priceTier === 'costlier' ? 'bg-accentPrimary text-black shadow-[0_0_15px_rgba(210,248,91,0.4)] font-bold' : 'bg-white/5 text-textPrimary hover:bg-white/10 border border-white/5'}`}
              >
                $500+
              </motion.button>
            </div>

            {/* Inputs */}
            <form onSubmit={handleFormSubmit} className="flex flex-col md:flex-row gap-4 items-stretch md:items-center">
              
              {/* Target Query */}
              <div className="flex-1 bg-black/20 border border-white/10 rounded-[1.25rem] p-4 flex flex-col focus-within:border-accentPrimary/50 focus-within:bg-black/30 transition-colors">
                <label className="text-[10px] uppercase font-bold text-textMuted tracking-wider mb-1 ml-1">Target Sound</label>
                <input 
                  type="text" 
                  placeholder="e.g. 'Very bassy but minimal treble'"
                  className="w-full bg-transparent text-textPrimary font-body font-medium text-lg outline-none placeholder-textPrimary/30 px-1"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>

              {/* Advanced EQ Scroll Button */}
              <motion.button 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.96 }}
                type="button"
                onClick={scrollToAdvancedEq}
                className="text-left bg-black/20 border border-white/10 rounded-[1.25rem] p-4 flex flex-col min-w-[220px] transition-colors cursor-pointer hover:bg-black/30 hover:border-accentPrimary/40 group"
              >
                <label className="text-[10px] uppercase font-bold text-textMuted tracking-wider mb-1 ml-1 cursor-pointer flex items-center justify-between">
                  <span>Advanced EQ</span>
                  <SlidersHorizontal size={12} className="text-accentPrimary" />
                </label>
                <div className="text-textPrimary font-body font-medium text-lg px-1 mt-0.5 group-hover:text-accentPrimary transition-colors flex items-center gap-2">
                  <span>Tune Sliders</span>
                  <span className="text-xs text-accentPrimary">↓</span>
                </div>
              </motion.button>

              {/* Search Submit Button */}
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.92 }}
                type="submit"
                disabled={loading}
                className="w-full md:w-[76px] h-[76px] shrink-0 bg-accentPrimary rounded-[1.25rem] flex items-center justify-center text-black hover:brightness-110 transition-all shadow-[0_0_20px_rgba(210,248,91,0.4)] disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
              >
                {loading ? (
                  <div className="w-7 h-7 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <MagnifyingGlass size={32} weight="bold" />
                )}
              </motion.button>
            </form>
          </div>
        </div>
      </div>

      {/* Search Results Section - Transparent Outer Section */}
      <AnimatePresence>
        {(results.length > 0 || error || loading) && (
          <motion.div 
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="w-full bg-transparent relative z-10 px-6 md:px-12 py-16"
          >
            <div className="max-w-[1200px] mx-auto">
              
              {error && <div className="text-red-400 font-mono mb-8 p-4 bg-red-500/10 rounded-xl border border-red-500/20">{error}</div>}

              {/* Results Grid */}
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
                      <motion.button
                        whileHover={{ scale: 1.04 }}
                        whileTap={{ scale: 0.95 }}
                        type="button"
                        onClick={handleSuggestMore}
                        disabled={loadingMore}
                        className="px-8 py-4 bg-white/5 border border-white/10 hover:border-accentPrimary hover:bg-accentPrimary/5 text-textPrimary hover:text-accentPrimary font-mono uppercase tracking-wider text-xs rounded-xl transition-all duration-300 disabled:opacity-50 cursor-pointer"
                      >
                        {loadingMore ? 'Loading...' : 'Load More IEMs'}
                      </motion.button>
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

      {/* Advanced Acoustic EQ Sliders Section - Transparent Outer Section */}
      <section id="advanced-eq" className="w-full bg-transparent px-6 md:px-12 py-20 relative z-10">
        <div className="max-w-[1200px] mx-auto">
          <div className="mb-10 text-center">
            <span className="font-mono text-xs text-accentPrimary uppercase tracking-widest block mb-2">Manual Tuning</span>
            <h2 className="font-display text-3xl md:text-5xl font-bold text-textPrimary tracking-tight mb-3 drop-shadow-lg">
              Advanced Acoustic Configuration
            </h2>
            <p className="font-body text-textMuted text-base md:text-lg max-w-2xl mx-auto drop-shadow">
              Adjust individual frequency band sliders (sub-bass, presence, air, tonal tilt) to search for custom acoustic profiles directly.
            </p>
          </div>

          <EqSliderGrid 
            exactFeatures={exactFeatures} 
            setExactFeatures={setExactFeatures} 
            runSearch={(q, topK, isMore, pTier) => runSearch(q, topK, isMore, pTier, true)} 
            loading={loading} 
            query={query} 
          />
        </div>
      </section>

      {/* How It Works Section - Transparent Outer Section */}
      <section id="how-it-works" className="w-full bg-transparent px-6 md:px-12 py-20 relative z-10">
        <div className="max-w-[1400px] mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="font-mono text-xs text-accentPrimary uppercase tracking-widest block mb-3">Engine Architecture</span>
            <h2 className="font-display text-4xl md:text-5xl font-bold text-textPrimary tracking-tight mb-4 drop-shadow-lg">
              AI-Powered Acoustic Search Engine
            </h2>
            <p className="font-body text-textMuted text-base md:text-lg leading-relaxed drop-shadow">
              AcousticSearch bridges natural language queries with physical IEM frequency response curves using Google Gemini, high-dimensional vector space, and hybrid math.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-[#0F141C]/70 border border-white/10 rounded-[2rem] p-8 hover:border-accentPrimary/40 transition-all duration-300 backdrop-blur-2xl shadow-2xl relative overflow-hidden group">
              <div className="w-12 h-12 rounded-2xl bg-accentPrimary/10 border border-accentPrimary/20 flex items-center justify-center text-accentPrimary mb-6 group-hover:scale-110 transition-transform">
                <Cpu size={28} weight="bold" />
              </div>
              <h3 className="font-display text-xl font-bold text-textPrimary mb-3">1. Target Extraction</h3>
              <p className="font-body text-textMuted text-sm leading-relaxed">
                Google Gemini translates your sound description into a 10-dimensional acoustic feature profile (sub-bass, mids, treble, air, tonal tilt, sibilance risk).
              </p>
            </div>

            <div className="bg-[#0F141C]/70 border border-white/10 rounded-[2rem] p-8 hover:border-accentPrimary/40 transition-all duration-300 backdrop-blur-2xl shadow-2xl relative overflow-hidden group">
              <div className="w-12 h-12 rounded-2xl bg-accentPrimary/10 border border-accentPrimary/20 flex items-center justify-center text-accentPrimary mb-6 group-hover:scale-110 transition-transform">
                <Target size={28} weight="bold" />
              </div>
              <h3 className="font-display text-xl font-bold text-textPrimary mb-3">2. Vector Search</h3>
              <p className="font-body text-textMuted text-sm leading-relaxed">
                Dense 384-dimensional MiniLM embeddings perform cosine similarity searches over Supabase <code className="font-mono text-accentPrimary text-xs">pgvector</code> datasets of measured IEMs.
              </p>
            </div>

            <div className="bg-[#0F141C]/70 border border-white/10 rounded-[2rem] p-8 hover:border-accentPrimary/40 transition-all duration-300 backdrop-blur-2xl shadow-2xl relative overflow-hidden group">
              <div className="w-12 h-12 rounded-2xl bg-accentPrimary/10 border border-accentPrimary/20 flex items-center justify-center text-accentPrimary mb-6 group-hover:scale-110 transition-transform">
                <Waves size={28} weight="bold" />
              </div>
              <h3 className="font-display text-xl font-bold text-textPrimary mb-3">3. Hybrid Reranking</h3>
              <p className="font-body text-textMuted text-sm leading-relaxed">
                Candidates are locally re-ranked using a hybrid formula combining semantic distance and acoustic Euclidean feature distance (<span className="font-mono text-accentPrimary">α = 0.5</span>).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQs Section - Transparent Outer Section */}
      <section id="faq" className="w-full bg-transparent px-6 md:px-12 py-20 relative z-10">
        <div className="max-w-[1000px] mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="font-mono text-xs text-accentPrimary uppercase tracking-widest block mb-3">Got Questions?</span>
            <h2 className="font-display text-4xl font-bold text-textPrimary tracking-tight mb-4 drop-shadow-lg">
              Frequently Asked Questions
            </h2>
            <p className="font-body text-textMuted text-base drop-shadow">
              Everything you need to know about AcousticSearch, sound matching, and frequency response curves.
            </p>
          </div>

          <div className="space-y-4">
            {FAQ_ITEMS.map((item, idx) => (
              <FaqAccordionItem key={idx} question={item.q} answer={item.a} />
            ))}
          </div>
        </div>
      </section>

      {/* Floating Compare Action Drawer at Bottom */}
      <AnimatePresence>
        {compareCart.length > 0 && (
          <motion.div 
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            transition={{ type: "spring", stiffness: 200, damping: 25 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-[#0B0F15]/90 backdrop-blur-2xl border border-accentPrimary/50 shadow-[0_20px_50px_rgba(210,248,91,0.3)] rounded-full px-8 py-4 flex items-center gap-6 z-50"
          >
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-accentPrimary animate-pulse"></div>
              <span className="font-mono text-xs text-textPrimary uppercase tracking-widest font-semibold">
                {compareCart.length} {compareCart.length === 1 ? 'IEM' : 'IEMs'} Selected
              </span>
            </div>

            <motion.button 
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.94 }}
              onClick={handleNavCompareClick}
              className="px-6 py-2.5 bg-accentPrimary text-black rounded-full font-mono text-xs uppercase tracking-wider font-bold hover:brightness-110 transition-all shadow-lg cursor-pointer flex items-center gap-2"
            >
              <ArrowsLeftRight size={16} weight="bold" />
              Compare Now
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <footer className="w-full bg-black/60 backdrop-blur-2xl border-t border-white/10 px-6 md:px-12 py-16 relative z-10 text-textMuted">
        <div className="max-w-[1400px] mx-auto grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          <div className="md:col-span-2">
            <a href="/" className="font-display font-bold text-2xl tracking-tight text-textPrimary block mb-4">
              Acoustic<span className="text-accentPrimary">Search.</span>
            </a>
            <p className="font-body text-sm text-textMuted max-w-sm leading-relaxed mb-6">
              AI-powered In-Ear Monitor recommendation engine combining natural language processing, vector embeddings, and acoustic curve math.
            </p>
            <div className="flex flex-wrap gap-2 text-[10px] font-mono uppercase tracking-wider text-textMuted">
              <span className="px-2.5 py-1 bg-white/5 rounded border border-white/5">FastAPI</span>
              <span className="px-2.5 py-1 bg-white/5 rounded border border-white/5">Supabase pgvector</span>
              <span className="px-2.5 py-1 bg-white/5 rounded border border-white/5">Gemini API</span>
              <span className="px-2.5 py-1 bg-white/5 rounded border border-white/5">Astro v5</span>
            </div>
          </div>

          <div>
            <h4 className="font-mono text-xs text-textPrimary uppercase tracking-widest mb-4">Navigation</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="/" className="hover:text-accentPrimary transition-colors">Search Engine</a></li>
              <li><a href="#how-it-works" className="hover:text-accentPrimary transition-colors">How It Works</a></li>
              <li><a href="#advanced-eq" className="hover:text-accentPrimary transition-colors">Advanced EQ</a></li>
              <li><a href="#faq" className="hover:text-accentPrimary transition-colors">FAQs</a></li>
              <li><a href="/about" className="hover:text-accentPrimary transition-colors">About IEMs</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-mono text-xs text-textPrimary uppercase tracking-widest mb-4">Acoustic Traits</h4>
            <div className="flex flex-wrap gap-1.5 text-xs font-mono">
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">Sub-bass</span>
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">Warm Mids</span>
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">Airy Treble</span>
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">V-shaped</span>
              <span className="px-2 py-1 bg-white/5 rounded text-textMuted">Neutral</span>
            </div>
          </div>
        </div>

        <div className="max-w-[1400px] mx-auto border-t border-white/5 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-mono">
          <p>© {new Date().getFullYear()} AcousticSearch. All rights reserved.</p>
          <p className="text-textMuted/60">Crafted for Audiophiles & Music Enthusiasts</p>
        </div>
      </footer>

    </div>
  );
}
