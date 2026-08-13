import React, { useState, useEffect } from 'react';
import MiniChart from './MiniChart';
import ResultCard from './ResultCard';
import ErrorBoundary from './ErrorBoundary';

export default function ProductApp() {
  const [iem, setIem] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const name = params.get('name');
    
    if (!name) {
      setError("No IEM specified");
      setLoading(false);
      return;
    }

    const fetchIem = async () => {
      try {
        const apiBase = import.meta.env.PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const res = await fetch(`${apiBase}/iem/${encodeURIComponent(name)}`);
        if (!res.ok) throw new Error('Failed to fetch IEM details');
        const data = await res.json();
        
        if (data.error) throw new Error(data.error);
        
        setIem(data.iem);
        
        // Similar items don't have a 'score' from hybrid matching by default from this endpoint, 
        // we'll just mock scores or leave them blank for the ResultCard.
        const similarWithMockScores = (data.similar || []).map(s => ({
          ...s,
          score: 1.0, 
          semantic_score: 1.0, 
          acoustic_score: 1.0, 
          contributors: ['SIMILAR MATCH']
        }));
        setSimilar(similarWithMockScores);
      } catch (err) {
        const isNetworkErr = err.message?.toLowerCase().includes('failed to fetch');
        const displayErr = isNetworkErr
          ? `Unable to connect to API. Please verify python server.py is running on port 8000.`
          : err.message;
        setError(displayErr);
      } finally {
        setLoading(false);
      }
    };

    fetchIem();
  }, []);

  if (loading) return <div className="text-center mt-20 text-accentPrimary font-mono uppercase">Loading Acoustic Profile...</div>;
  if (error) return <div className="text-center mt-20 text-red-500 font-mono uppercase">Error: {error}</div>;
  if (!iem) return null;

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto mt-12 px-4 pb-16">
      
      {/* Header */}
      <div className="mb-8 border-b border-bgBorder pb-6 flex flex-col md:flex-row justify-between items-start md:items-end">
        <div>
          <button 
            onClick={() => {
              if (window.history.length > 1) {
                window.history.back();
              } else {
                window.location.href = '/';
              }
            }} 
            className="font-mono text-xs text-textMuted hover:text-accentPrimary uppercase tracking-widest mb-4 inline-block bg-transparent border-none p-0 cursor-pointer"
          >
            &larr; Back to Search
          </button>
          <h1 className="font-display text-4xl text-textPrimary tracking-wide uppercase">{iem.name}</h1>
          <div className="mt-3 flex items-center gap-4">
            {iem.features?.price && (
              <span className="font-mono text-2xl text-accentPrimary tracking-wider">${iem.features.price}</span>
            )}
            {iem.features?.acoustic_profile_source === 'autoeq' && (
              <span className="px-3 py-1 bg-green-500/20 text-green-400 border border-green-500/30 rounded text-[10px] font-mono uppercase tracking-widest">
                AutoEQ Verified Math
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Left Col: Description & Features */}
        <div className="lg:col-span-1 space-y-8">
          <div>
            <h3 className="font-mono text-xs text-textMuted uppercase tracking-widest mb-3 border-b border-bgBorder pb-2">Description</h3>
            <p className="font-body text-textPrimary leading-relaxed text-sm whitespace-pre-wrap">
              {iem.description}
            </p>
          </div>
          
          <div>
             <h3 className="font-mono text-xs text-textMuted uppercase tracking-widest mb-3 border-b border-bgBorder pb-2">Extracted Acoustic Targets</h3>
             <ul className="space-y-2">
               {['sub_bass', 'bass', 'low_mids', 'mids', 'presence', 'treble', 'air'].map(band => (
                 <li key={band} className="flex justify-between items-center text-sm font-mono">
                   <span className="text-textMuted uppercase">{band.replace('_', ' ')}</span>
                   <span className="text-textPrimary">
                     {iem.features[band] > 0 ? '+' : ''}{(iem.features[band] || 0).toFixed(1)} dB
                   </span>
                 </li>
               ))}
             </ul>
          </div>
        </div>

        {/* Right Col: Big Chart */}
        <div className="lg:col-span-2">
          <div className="bg-bgSurface border border-bgBorder rounded-xl p-6 shadow-2xl">
            <h3 className="font-mono text-xs text-textMuted uppercase tracking-widest mb-6">Frequency Response Profile</h3>
            {/* We scale the MiniChart by passing it inside a larger container. MiniChart is SVG so it scales perfectly. */}
            <div className="transform scale-[1.2] origin-top-left mb-16 w-[80%]">
              <MiniChart features={iem.features} />
            </div>
          </div>
        </div>
      </div>

      {/* Similar Items */}
      {similar.length > 0 && (
        <div className="mt-20">
          <h3 className="font-display text-2xl text-textPrimary tracking-wide uppercase mb-8 border-b border-bgBorder pb-2">
            Similar Sound Signatures
          </h3>
          <div className="space-y-8">
            {similar.map((sim, idx) => (
              <ResultCard key={sim.name} result={sim} rank={idx + 1} />
            ))}
          </div>
        </div>
      )}

      </div>
    </ErrorBoundary>
  );
}
