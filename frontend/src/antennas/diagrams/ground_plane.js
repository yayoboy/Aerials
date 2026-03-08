import { DiagramSVG, VWire, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { radial_length_mm = 490, num_radials = 4, radial_angle_deg = 45, frequency_mhz = 146 } = params;
  const cx = 260, baseY = 130;
  const scale = Math.min(80 / radial_length_mm, 0.25);
  const rLen = radial_length_mm * scale;
  const vLen = rLen;
  const angleRad = radial_angle_deg * Math.PI / 180;

  const radials = [];
  for (let i = 0; i < num_radials; i++) {
    const theta = (i / num_radials) * 2 * Math.PI + Math.PI/4;
    radials.push({ x: cx + Math.cos(theta) * rLen, y: baseY + Math.sin(theta) * rLen * Math.sin(angleRad) });
  }

  return (
    <DiagramSVG>
      {radials.map((r, i) => (
        <line key={i} x1={cx} y1={baseY} x2={r.x} y2={r.y} stroke="#58a6ff" strokeWidth="2.5" strokeLinecap="round" />
      ))}
      <VWire x={cx} y1={baseY - vLen} y2={baseY} />
      <FeedDot x={cx} y={baseY} />
      <VDim x={cx - 22} y1={baseY - vLen} y2={baseY} label={`λ/4 = ${radial_length_mm} mm`} />
      <text x={cx + 14} y={baseY + 24} fill="#8b949e" fontSize="10">{num_radials} radiali, {radial_angle_deg}°</text>
    </DiagramSVG>
  );
}
