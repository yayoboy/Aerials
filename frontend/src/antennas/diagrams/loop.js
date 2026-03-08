import { DiagramSVG, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { perimeter_mm = 21400, shape = 'square', frequency_mhz = 14 } = params;
  const cx = 260, cy = 105;
  const size = 140;

  if (shape === 'square') {
    const half = size / 2;
    const feedX = cx, feedY = cy + half;
    return (
      <DiagramSVG>
        <rect x={cx - half} y={cy - half} width={size} height={size} fill="none" stroke="#58a6ff" strokeWidth="3" />
        <FeedDot x={feedX} y={feedY} />
        <text x={cx} y={cy} textAnchor="middle" fill="#8b949e" fontSize="11">λ = {perimeter_mm} mm</text>
        <text x={cx} y={cy + 16} textAnchor="middle" fill="#8b949e" fontSize="10">lato = {Math.round(perimeter_mm/4)} mm</text>
      </DiagramSVG>
    );
  }
  return (
    <DiagramSVG>
      <circle cx={cx} cy={cy} r={size/2} fill="none" stroke="#58a6ff" strokeWidth="3" />
      <FeedDot x={cx} y={cy + size/2} />
      <text x={cx} y={cy} textAnchor="middle" fill="#8b949e" fontSize="11">λ = {perimeter_mm} mm</text>
      <text x={cx} y={cy + 16} textAnchor="middle" fill="#8b949e" fontSize="10">⌀ = {Math.round(perimeter_mm/Math.PI)} mm</text>
    </DiagramSVG>
  );
}
