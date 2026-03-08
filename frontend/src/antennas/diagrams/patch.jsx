import { DiagramSVG, HDim, VDim, FeedDot } from './utils.jsx';

export function buildDiagram(params) {
  const { width_mm = 38, length_mm = 29, substrate_height_mm = 1.6, substrate_er = 4.4 } = params;
  const cx = 260, cy = 100;
  const scale = Math.min(200 / Math.max(width_mm, length_mm), 3);
  const W = width_mm * scale;
  const L = length_mm * scale;
  const subH = Math.max(substrate_height_mm * scale * 3, 8);

  return (
    <DiagramSVG>
      <rect x={cx - W/2 - 10} y={cy + L/2} width={W + 20} height={subH}
        fill="#1c2e4a" stroke="#30363d" strokeWidth="1" />
      <text x={cx} y={cy + L/2 + subH/2 + 4} textAnchor="middle" fill="#8b949e" fontSize="10">
        εr = {substrate_er} (h = {substrate_height_mm} mm)
      </text>
      <rect x={cx - W/2 - 10} y={cy + L/2 + subH} width={W + 20} height={5}
        fill="#58a6ff" stroke="none" />
      <rect x={cx - W/2} y={cy - L/2} width={W} height={L}
        fill="rgba(88,166,255,0.15)" stroke="#58a6ff" strokeWidth="2.5" />
      <FeedDot x={cx} y={cy + L/2} label="feed (edge)" />
      <HDim x1={cx - W/2} x2={cx + W/2} y={cy - L/2 - 18} label={`W = ${width_mm} mm`} />
      <VDim x={cx + W/2 + 18} y1={cy - L/2} y2={cy + L/2} label={`L = ${length_mm} mm`} left={false} />
    </DiagramSVG>
  );
}
