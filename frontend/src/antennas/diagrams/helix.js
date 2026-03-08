import { DiagramSVG, VDim, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { diameter_mm = 40, pitch_mm = 30, turns = 8, frequency_mhz = 2400 } = params;
  const cx = 260, baseY = 180;
  const scaleD = Math.min(120 / diameter_mm, 2);
  const scaleP = Math.min(120 / (pitch_mm * turns), 1.5);
  const r = diameter_mm / 2 * scaleD;
  const totalH = pitch_mm * turns * scaleP;
  const points = [];
  for (let i = 0; i <= turns * 12; i++) {
    const t = (i / 12) * 2 * Math.PI;
    const x = cx + r * Math.cos(t);
    const y = baseY - (i / (turns * 12)) * totalH;
    points.push(`${x},${y}`);
  }

  return (
    <DiagramSVG>
      <polyline points={points.join(' ')} fill="none" stroke="#58a6ff" strokeWidth="2.5" />
      <FeedDot x={cx + r} y={baseY} />
      <VDim x={cx - r - 22} y1={baseY - totalH} y2={baseY} label={`${(pitch_mm * turns).toFixed(0)} mm`} />
      <HDim x1={cx - r} x2={cx + r} y={baseY - totalH - 18} label={`⌀ ${diameter_mm} mm`} />
      <text x={cx} y={baseY - totalH / 2} textAnchor="middle" fill="#8b949e" fontSize="10">{turns} spire</text>
    </DiagramSVG>
  );
}
