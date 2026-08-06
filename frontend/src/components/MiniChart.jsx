import React from 'react';

const BANDS = [
  { key: "sub_bass", label: "20" },
  { key: "bass", label: "60" },
  { key: "low_mids", label: "250" },
  { key: "mids", label: "500" },
  { key: "presence", label: "2k" },
  { key: "treble", label: "6k" },
  { key: "air", label: "10k" }
];

const Y_TICKS = [
  { db: 12, label: "+12" },
  { db: 6, label: "+6" },
  { db: 0, label: "0" },
  { db: -6, label: "-6" },
  { db: -12, label: "-12" }
];

export default function MiniChart({ features, targetFeatures }) {
  const width = 340;
  const height = 190;
  
  const paddingLeft = 32;
  const paddingRight = 30;
  const paddingTop = 24;
  const paddingBottom = 26;
  
  const innerWidth = width - paddingLeft - paddingRight;
  const innerHeight = height - paddingTop - paddingBottom;
  
  const mapY = (db) => {
    const clamped = Math.max(-12, Math.min(12, db));
    return paddingTop + innerHeight / 2 - (clamped / 12) * (innerHeight / 2);
  };
  
  const mapX = (index) => {
    return paddingLeft + (index / (BANDS.length - 1)) * innerWidth;
  };
  
  // Calculate points
  const points = BANDS.map((b, i) => ({
    x: mapX(i),
    y: mapY(features[b.key] || 0)
  }));

  // Create smooth Bezier curve
  const getSmoothPath = (pts) => {
    if (pts.length < 2) return '';
    let path = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const curr = pts[i];
      const next = pts[i + 1];
      const mx = (curr.x + next.x) / 2;
      path += ` C ${mx} ${curr.y}, ${mx} ${next.y}, ${next.x} ${next.y}`;
    }
    return path;
  };

  const linePath = getSmoothPath(points);
  const bottomY = paddingTop + innerHeight;
  const areaPath = `${linePath} L ${mapX(BANDS.length - 1)} ${bottomY} L ${mapX(0)} ${bottomY} Z`;

  return (
    <div className="w-full bg-[#080b10] border border-[#1d2636] rounded-lg p-2 relative select-none">
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible font-mono text-[10px]">
        <defs>
          {/* Red Glow Gradient Fill */}
          <linearGradient id="redGlowGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.45" />
            <stop offset="60%" stopColor="#ef4444" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Top-Left 'dB' Header */}
        <text x={paddingLeft - 24} y={14} fill="#8F9BAC" fontWeight="600" className="text-[11px]">dB</text>
        
        {/* Bottom-Right 'HZ' Header */}
        <text x={width - 24} y={height - 8} fill="#8F9BAC" fontWeight="600" className="text-[11px]">HZ</text>

        {/* Horizontal Gridlines & Y-Axis Labels */}
        {Y_TICKS.map((tick, i) => {
          const y = mapY(tick.db);
          return (
            <g key={i}>
              <line 
                x1={paddingLeft} 
                y1={y} 
                x2={width - paddingRight} 
                y2={y} 
                stroke={tick.db === 0 ? "#374151" : "#192231"} 
                strokeWidth={tick.db === 0 ? "1.5" : "1"} 
                strokeDasharray={tick.db === 0 ? "3 3" : "none"}
              />
              <text 
                x={paddingLeft - 6} 
                y={y + 3} 
                fill="#6B7280" 
                textAnchor="end"
              >
                {tick.label}
              </text>
            </g>
          );
        })}

        {/* Vertical Gridlines & X-Axis Frequency Labels */}
        {BANDS.map((b, i) => {
          const x = mapX(i);
          return (
            <g key={i}>
              <line 
                x1={x} 
                y1={paddingTop} 
                x2={x} 
                y2={bottomY} 
                stroke="#192231" 
                strokeWidth="1" 
              />
              <text 
                x={x} 
                y={height - 8} 
                fill="#6B7280" 
                textAnchor="middle"
              >
                {b.label}
              </text>
            </g>
          );
        })}

        {/* Gradient Red Fill under Curve */}
        <path d={areaPath} fill="url(#redGlowGradient)" />

        {/* Smooth Crimson Curve Line */}
        <path 
          d={linePath} 
          fill="none" 
          stroke="#ef4444" 
          strokeWidth="2.5" 
          strokeLinecap="round"
        />

        {/* Data points */}
        {points.map((pt, i) => (
          <circle key={i} cx={pt.x} cy={pt.y} r="2.5" fill="#080b10" stroke="#ef4444" strokeWidth="1.5" />
        ))}
      </svg>
    </div>
  );
}
