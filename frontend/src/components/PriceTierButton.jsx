import React from 'react';

export default function PriceTierButton({ tier, label, currentTier, onChange }) {
  const isSelected = currentTier === tier;
  
  return (
    <button
      type="button"
      onClick={() => onChange(tier)}
      className={`px-4 py-2 font-mono text-xs uppercase tracking-wider rounded-lg border transition-all duration-200 ${
        isSelected
          ? 'bg-accentPrimary text-bgSurface font-bold border-accentPrimary shadow-lg'
          : 'bg-bgSurface text-textMuted border-bgBorder hover:border-accentPrimary/50 hover:text-textPrimary'
      }`}
    >
      {label}
    </button>
  );
}
