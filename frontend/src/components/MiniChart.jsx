import React from 'react';

const BANDS = ["sub_bass", "bass", "low_mids", "mids", "presence", "treble", "air"];

export default function MiniChart({ features, targetFeatures }) {
  // SVG drawing logic
  const width = 200;
  const height = 100;
  const paddingX = 10;
  const paddingY = 20;
  
  const innerWidth = width - 2 * paddingX;
  const innerHeight = height - 2 * paddingY;
  
  // Map deviation dB to Y pixel coordinate
  // Let's assume max deviation is +/- 10dB
  const mapY = (db) => {
    // Clamp db between -12 and +12
    const clamped = Math.max(-12, Math.min(12, db));
    // 0 dB is at innerHeight / 2
    return paddingY + innerHeight / 2 - (clamped / 12) * (innerHeight / 2);
  };
  
  const mapX = (index) => {
    return paddingX + (index / (BANDS.length - 1)) * innerWidth;
  };
  
  // Generate SVG path strings
  const generatePath = (featureSource) => {
    return BANDS.map((band, i) => {
      const x = mapX(i);
      const y = mapY(featureSource[band] || 0);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };
  
  const iemPath = generatePath(features);
  const targetPath = generatePath(targetFeatures);
  const zeroLineY = mapY(0);

  return (
    <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="mt-4">
      {/* Grid lines */}
      {[...Array(5)].map((_, i) => {
        const y = paddingY + (i / 4) * innerHeight;
        return (
          <line key={i} x1={paddingX} y1={y} x2={width - paddingX} y2={y} stroke="#1F2736" strokeWidth="1" />
        );
      })}
      
      {/* 0dB Neutral Line */}
      <line x1={paddingX} y1={zeroLineY} x2={width - paddingX} y2={zeroLineY} stroke="#4C566A" strokeWidth="1" strokeDasharray="4 4" />
      
      {/* Target Line (Ghosted) */}
      <path d={targetPath} fill="none" stroke="#4C566A" strokeWidth="1.5" strokeOpacity="0.5" />
      
      {/* IEM Curve */}
      <path d={iemPath} fill="none" stroke="#FF8A4C" strokeWidth="2.5" />
      
      {/* Data points */}
      {BANDS.map((band, i) => (
        <circle key={i} cx={mapX(i)} cy={mapY(features[band] || 0)} r="3" fill="#0B0F15" stroke="#FF8A4C" strokeWidth="1.5" />
      ))}
    </svg>
  );
}
