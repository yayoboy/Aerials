// Shared SVG drawing helpers for antenna construction diagrams
// All diagrams use viewBox="0 0 520 220"

export const VW = 520;
export const VH = 220;

// Horizontal dimension line with arrows and label
export function HDim({ x1, x2, y, label, above = true }) {
  const mx = (x1 + x2) / 2;
  const ly = above ? y - 8 : y + 16;
  const id = `arr-${Math.random().toString(36).slice(2)}`;
  return (
    <>
      <defs>
        <marker id={`${id}e`} viewBox="0 0 8 8" refX="8" refY="4" markerWidth="5" markerHeight="5" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
        <marker id={`${id}s`} viewBox="0 0 8 8" refX="0" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
      </defs>
      <line x1={x1} y1={y} x2={x2} y2={y} stroke="#6e7681" strokeWidth="0.8"
        markerStart={`url(#${id}s)`} markerEnd={`url(#${id}e)`} />
      <line x1={x1} y1={y-4} x2={x1} y2={y+4} stroke="#6e7681" strokeWidth="0.8" />
      <line x1={x2} y1={y-4} x2={x2} y2={y+4} stroke="#6e7681" strokeWidth="0.8" />
      <text x={mx} y={ly} textAnchor="middle" fill="#8b949e" fontSize="11">{label}</text>
    </>
  );
}

// Vertical dimension line
export function VDim({ x, y1, y2, label, left = true }) {
  const my = (y1 + y2) / 2;
  const lx = left ? x - 8 : x + 8;
  const anchor = left ? 'end' : 'start';
  const id = `arr-${Math.random().toString(36).slice(2)}`;
  return (
    <>
      <defs>
        <marker id={`${id}e`} viewBox="0 0 8 8" refX="8" refY="4" markerWidth="5" markerHeight="5" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
        <marker id={`${id}s`} viewBox="0 0 8 8" refX="0" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
      </defs>
      <line x1={x} y1={y1} x2={x} y2={y2} stroke="#6e7681" strokeWidth="0.8"
        markerStart={`url(#${id}s)`} markerEnd={`url(#${id}e)`} />
      <line x1={x-4} y1={y1} x2={x+4} y2={y1} stroke="#6e7681" strokeWidth="0.8" />
      <line x1={x-4} y1={y2} x2={x+4} y2={y2} stroke="#6e7681" strokeWidth="0.8" />
      <text x={lx} y={my + 4} textAnchor={anchor} fill="#8b949e" fontSize="11">{label}</text>
    </>
  );
}

// Horizontal wire (conductor)
export function HWire({ x1, x2, y, thick = 3 }) {
  return <line x1={x1} y1={y} x2={x2} y2={y} stroke="#58a6ff" strokeWidth={thick} strokeLinecap="round" />;
}

// Vertical wire
export function VWire({ x, y1, y2, thick = 3 }) {
  return <line x1={x} y1={y1} x2={x} y2={y2} stroke="#58a6ff" strokeWidth={thick} strokeLinecap="round" />;
}

// Feed point marker
export function FeedDot({ x, y, label = 'feed' }) {
  return (
    <>
      <circle cx={x} cy={y} r="5" fill="#f85149" />
      <text x={x} y={y + 17} textAnchor="middle" fill="#f85149" fontSize="10">{label}</text>
    </>
  );
}

// SVG wrapper with dark background
export function DiagramSVG({ children }) {
  return (
    <svg viewBox={`0 0 ${VW} ${VH}`} style={{ width: '100%', height: '100%', minHeight: '220px', display: 'block' }} preserveAspectRatio="xMidYMid meet" overflow="visible">
      <rect width={VW} height={VH} fill="transparent" />
      {children}
    </svg>
  );
}
