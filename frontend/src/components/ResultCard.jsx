import React from 'react';
import MiniChart from './MiniChart';

export default function ResultCard({ result, rank, isCompared, onToggleCompare }) {
  return (
    <div className="bg-bgSurface border border-bgBorder rounded-xl p-6 flex flex-col md:flex-row gap-8 hover:border-accentPrimary/50 transition-colors duration-300 relative">
      
      {/* Left Column: Metadata */}
      <div className="flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-baseline justify-between mb-2">
            <div className="flex items-baseline gap-3">
              <span className="font-mono text-accentPrimary font-bold text-xl">0{rank}</span>
              <a href={`/iem?name=${encodeURIComponent(result.name)}`} className="font-display text-2xl text-textPrimary tracking-wide uppercase hover:text-accentPrimary transition-colors cursor-pointer">
                {result.name}
              </a>
            </div>
            {result.features?.price && (
              <span className="font-mono text-textPrimary text-xl tracking-wider">
                ${result.features.price}
              </span>
            )}
          </div>
          
          {/* Explanation Badges */}
          <div className="flex flex-wrap gap-2 mb-4">
            {result.contributors.map((c, i) => (
              <span key={i} className="px-3 py-1 bg-accentSecondary/20 text-accentPrimary border border-accentPrimary/20 rounded text-xs font-mono uppercase tracking-widest">
                {c}
              </span>
            ))}
          </div>

          <p className="font-body text-textMuted leading-relaxed text-sm">
            {result.description}
          </p>
        </div>

        {/* Scores */}
        <div className="mt-6 flex gap-6 border-t border-bgBorder/50 pt-4">
          <div>
            <div className="text-[10px] text-textMuted uppercase tracking-widest font-mono mb-1">Hybrid Match</div>
            <div className="font-mono text-xl text-textPrimary">{(result.score * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[10px] text-textMuted uppercase tracking-widest font-mono mb-1">Semantic NLP</div>
            <div className="font-mono text-sm text-textMuted">{(result.semantic_score * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-[10px] text-textMuted uppercase tracking-widest font-mono mb-1">Acoustic Math</div>
            <div className="font-mono text-sm text-textMuted">{(result.acoustic_score * 100).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Right Column: High Fidelity FR Oscilloscope Chart */}
      <div className="w-full md:w-80 flex flex-col justify-center">
        <MiniChart features={result.features} targetFeatures={result.target_features} />
      </div>

      {/* Compare Button (Bottom Right) */}
      {onToggleCompare && (
        <button
          onClick={onToggleCompare}
          className={`absolute bottom-6 right-6 px-4 py-2 font-mono text-xs uppercase tracking-wider rounded border transition-all duration-200 ${
            isCompared
              ? 'bg-accentPrimary/20 text-accentPrimary border-accentPrimary/50'
              : 'bg-transparent text-textMuted border-bgBorder hover:border-accentPrimary/50 hover:text-accentPrimary'
          }`}
        >
          {isCompared ? 'Added to Compare' : '+ Compare'}
        </button>
      )}

    </div>
  );
}
