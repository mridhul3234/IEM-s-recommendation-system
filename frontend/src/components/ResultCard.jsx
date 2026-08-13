import React, { useState } from 'react';
import { motion } from 'framer-motion';
import MiniChart from './MiniChart';

export default function ResultCard({ result, rank, isCompared, onToggleCompare }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const MAX_DESC_LENGTH = 160;
  const description = result.description || '';
  const needsTruncation = description.length > MAX_DESC_LENGTH;
  const displayDescription = needsTruncation && !isExpanded
    ? `${description.slice(0, MAX_DESC_LENGTH).trim()}...`
    : description;

  return (
    <div className="bg-[#0F141C]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 flex flex-col justify-between hover:border-accentPrimary/40 transition-all duration-300 relative overflow-hidden h-full shadow-xl">
      
      {/* Top Section: Metadata & Scores */}
      <div className="flex flex-col flex-1 justify-between mb-4">
        <div>
          {/* Rank, Name & Price Header */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex items-baseline gap-2.5 min-w-0">
              <span className="font-mono text-accentPrimary font-bold text-lg shrink-0">
                {rank < 10 ? `0${rank}` : rank}
              </span>
              <a 
                href={`/iem?name=${encodeURIComponent(result.name)}`} 
                onClick={() => {
                  try {
                    const existing = JSON.parse(sessionStorage.getItem('last_search_state') || '{}');
                    existing.scrollY = window.scrollY;
                    sessionStorage.setItem('last_search_state', JSON.stringify(existing));
                  } catch (e) {}
                }}
                className="font-display text-xl font-bold text-textPrimary tracking-wide uppercase hover:text-accentPrimary transition-colors cursor-pointer truncate"
                title={result.name}
              >
                {result.name}
              </a>
            </div>
            {result.features?.price !== undefined && (
              <span className="font-mono text-accentPrimary font-bold text-lg tracking-wider shrink-0">
                ${result.features.price}
              </span>
            )}
          </div>
          
          {/* Explanation Badges */}
          {result.contributors && result.contributors.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {result.contributors.map((c, i) => (
                <span key={i} className="px-2.5 py-0.5 bg-accentPrimary/10 text-accentPrimary border border-accentPrimary/20 rounded-md text-[10px] font-mono uppercase tracking-widest font-semibold">
                  {c}
                </span>
              ))}
            </div>
          )}

          {/* Truncated Description */}
          <div className="mb-4">
            <p className="font-body text-textMuted leading-relaxed text-sm">
              {displayDescription}
            </p>
            {needsTruncation && (
              <button
                type="button"
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-1.5 inline-flex items-center gap-1 font-mono text-[11px] font-semibold text-accentPrimary hover:underline uppercase tracking-wider cursor-pointer bg-transparent border-none p-0"
              >
                {isExpanded ? 'Show Less ↑' : 'Read More ↓'}
              </button>
            )}
          </div>
        </div>

        {/* Scores Breakdown */}
        <div className="grid grid-cols-3 gap-2 border-t border-white/10 pt-3 mt-auto">
          <div>
            <div className="text-[9px] text-textMuted uppercase tracking-widest font-mono mb-0.5">Hybrid Match</div>
            <div className="font-mono text-base font-bold text-textPrimary">{(result.score * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[9px] text-textMuted uppercase tracking-widest font-mono mb-0.5">Semantic NLP</div>
            <div className="font-mono text-xs text-textMuted">{(result.semantic_score * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[9px] text-textMuted uppercase tracking-widest font-mono mb-0.5">Acoustic Math</div>
            <div className="font-mono text-xs text-textMuted">{(result.acoustic_score * 100).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Bottom Section: High Fidelity FR Oscilloscope Chart & Compare Button */}
      <div className="w-full flex flex-col items-center gap-3 pt-3 border-t border-white/10 mt-auto">
        <div className="w-full max-w-[340px] mx-auto overflow-hidden rounded-lg">
          <MiniChart features={result.features} targetFeatures={result.target_features} />
        </div>
        
        {onToggleCompare && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onToggleCompare(result.name)}
            className={`w-full py-2.5 px-4 font-mono text-xs uppercase tracking-wider rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-center gap-2 ${
              isCompared
                ? 'bg-accentPrimary text-black border-accentPrimary font-bold shadow-[0_0_15px_rgba(210,248,91,0.4)]'
                : 'bg-white/5 text-textMuted border-white/10 hover:border-accentPrimary/50 hover:text-accentPrimary hover:bg-white/10'
            }`}
          >
            {isCompared ? '✓ Added to Compare' : '+ Compare'}
          </motion.button>
        )}
      </div>

    </div>
  );
}
