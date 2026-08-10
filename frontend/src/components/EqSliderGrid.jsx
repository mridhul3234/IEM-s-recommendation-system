import React from 'react';
import { motion } from 'framer-motion';

export default function EqSliderGrid({ exactFeatures, setExactFeatures, runSearch, loading, query }) {
  return (
    <div className="max-w-5xl mx-auto mb-12 p-8 md:p-12 bg-[#0F141C]/70 backdrop-blur-2xl border border-white/10 rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.6)]">
      <div className="text-center mb-10 text-sm text-textMuted font-mono">
        Manually draw your exact acoustic target profile in decibels (dB). <br/>
        <span className="text-textMuted/60 text-xs">Note: Semantic text search is bypassed when using this mode.</span>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-5 gap-y-12 gap-x-6">
        {Object.keys(exactFeatures).map((key) => (
          <div key={key} className="flex flex-col items-center">
            <label className="text-xs font-mono text-accentPrimary uppercase tracking-widest mb-4 h-8 text-center flex items-center font-semibold">
              {key.replace(/_/g, ' ')}
            </label>
            <div className="h-40 flex items-center justify-center">
              <input 
                type="range"
                min={key.includes('sibilance') ? "0" : "-10"} 
                max="10" 
                step="0.5"
                value={exactFeatures[key]}
                onChange={(e) => setExactFeatures({...exactFeatures, [key]: parseFloat(e.target.value)})}
                className="w-40 -rotate-90 appearance-none bg-white/10 h-2 rounded-full outline-none cursor-pointer accent-[#D2F85B]"
              />
            </div>
            <div className="text-xs font-mono text-textPrimary mt-4 bg-white/5 px-3.5 py-1.5 rounded-lg border border-white/10 font-semibold">
              {exactFeatures[key] > 0 ? '+' : ''}{exactFeatures[key].toFixed(1)} dB
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-12 flex justify-center">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => runSearch(query)}
          disabled={loading}
          className="px-8 py-3.5 bg-accentPrimary text-black font-bold font-mono text-xs uppercase tracking-wider rounded-full shadow-[0_0_20px_rgba(210,248,91,0.4)] hover:brightness-110 transition-all duration-300 disabled:opacity-50 cursor-pointer"
        >
          {loading ? 'Calculating Matches...' : 'Find Acoustic Matches'}
        </motion.button>
      </div>
    </div>
  );
}
