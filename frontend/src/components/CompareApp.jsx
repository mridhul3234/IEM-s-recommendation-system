import React, { useState, useEffect } from 'react';
import MiniChart from './MiniChart';
import ErrorBoundary from './ErrorBoundary';
import { getApiBaseUrl } from '../lib/api';

const COLORS = ["#ef4444", "#3b82f6", "#10b981"]; // Red, Blue, Green

export default function CompareApp() {
  const [iems, setIems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const names = [];
    if (params.get('iem1')) names.push(params.get('iem1'));
    if (params.get('iem2')) names.push(params.get('iem2'));
    if (params.get('iem3')) names.push(params.get('iem3'));

    if (names.length < 2) {
      setError("Please select at least two IEMs to compare.");
      setLoading(false);
      return;
    }

    const fetchIems = async () => {
      try {
        const apiBase = getApiBaseUrl();
        const fetched = [];
        for (const name of names) {
          const res = await fetch(`${apiBase}/iem/${encodeURIComponent(name)}`);
          if (!res.ok) throw new Error(`Failed to fetch ${name}`);
          const data = await res.json();
          if (data.error) throw new Error(data.error);
          fetched.push(data.iem);
        }
        setIems(fetched);
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

    fetchIems();
  }, []);

  if (loading) return <div className="text-center mt-20 text-accentPrimary font-mono uppercase">Loading Models...</div>;
  if (error) return <div className="text-center mt-20 text-red-500 font-mono uppercase">Error: {error}</div>;
  if (iems.length < 2) return null;

  const datasets = iems.map((iem, i) => ({
    name: iem.name,
    features: iem.features,
    color: COLORS[i],
    isGlow: true
  }));

  return (
    <ErrorBoundary>
      <div className="max-w-6xl mx-auto mt-12 px-4 pb-16">
        
        {/* Header */}
        <div className="mb-8 border-b border-bgBorder pb-6">
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
          <h1 className="font-display text-4xl text-textPrimary tracking-wide uppercase">Versus Mode</h1>
          <p className="font-body text-textMuted mt-2">Direct A/B comparison of acoustic profiles.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-12">
          {/* Unified Chart */}
          <div className="lg:col-span-3 bg-bgSurface border border-bgBorder rounded-xl p-6 shadow-2xl flex flex-col justify-center min-h-[400px]">
            <h3 className="font-mono text-xs text-textMuted uppercase tracking-widest mb-6">Overlay Frequency Response</h3>
            <div className="transform scale-[1.3] origin-center mb-8 w-full max-w-full flex justify-center">
               <div className="w-[340px] h-[190px]">
                  <MiniChart datasets={datasets} />
               </div>
            </div>
            
            <div className="flex justify-center gap-6 mt-8 border-t border-bgBorder/50 pt-6">
              {datasets.map(ds => (
                <div key={ds.name} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: ds.color }}></div>
                  <span className="font-mono text-xs text-textPrimary">{ds.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Side-by-Side Comparison */}
          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-2 gap-4">
              {iems.map((iem, i) => (
                <div key={iem.name} className="bg-bgSurface border border-bgBorder rounded-xl p-4 flex flex-col">
                  <div className="w-full h-1 mb-3 rounded-full" style={{ backgroundColor: COLORS[i] }}></div>
                  <h3 className="font-display text-lg text-textPrimary leading-tight mb-2">{iem.name}</h3>
                  
                  <div className="mt-auto pt-4 space-y-3">
                    <div className="flex justify-between items-center border-b border-bgBorder/50 pb-1">
                      <span className="font-mono text-xs text-textMuted">Price</span>
                      <span className="font-mono text-sm text-textPrimary">${iem.features.price || '---'}</span>
                    </div>
                    
                    <div className="flex justify-between items-center border-b border-bgBorder/50 pb-1">
                      <span className="font-mono text-xs text-textMuted">Data Source</span>
                      <span className={`font-mono text-[10px] uppercase tracking-widest ${iem.features.acoustic_profile_source === 'autoeq' ? 'text-green-400' : 'text-accentPrimary'}`}>
                        {iem.features.acoustic_profile_source === 'autoeq' ? 'AutoEQ' : 'LLM Est.'}
                      </span>
                    </div>

                    <div className="pt-2">
                       <span className="font-mono text-xs text-textMuted uppercase">Sub-bass</span>
                       <div className="font-mono text-sm text-textPrimary">{(iem.features.sub_bass || 0).toFixed(1)} dB</div>
                    </div>
                    <div className="pt-1">
                       <span className="font-mono text-xs text-textMuted uppercase">Treble</span>
                       <div className="font-mono text-sm text-textPrimary">{(iem.features.treble || 0).toFixed(1)} dB</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </ErrorBoundary>
  );
}
