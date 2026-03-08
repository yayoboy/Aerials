import { DiagramSVG, HDim, FeedDot } from './utils.jsx';

export function buildDiagram(params) {
  const { length_mm = 20200, apex_angle_deg = 120, frequency_mhz = 7 } = params;
  const armLen = length_mm / 2;
  const angleRad = (apex_angle_deg / 2) * Math.PI / 180;
  const cx = 260, apexY = 50;
  const scale = 180 / armLen;
  const dx = Math.sin(angleRad) * armLen * scale;
  const dy = Math.cos(angleRad) * armLen * scale;

  return (
    <DiagramSVG>
      <line x1={cx} y1={apexY} x2={cx - dx} y2={apexY + dy} stroke="#58a6ff" strokeWidth="3" strokeLinecap="round" />
      <line x1={cx} y1={apexY} x2={cx + dx} y2={apexY + dy} stroke="#58a6ff" strokeWidth="3" strokeLinecap="round" />
      <line x1={cx - dx - 20} y1={apexY + dy} x2={cx + dx + 20} y2={apexY + dy} stroke="#6e7681" strokeWidth="1" strokeDasharray="4,3" />
      <FeedDot x={cx} y={apexY} label="feed (apex)" />
      <text x={cx} y={apexY + dy + 16} textAnchor="middle" fill="#8b949e" fontSize="10">GND</text>
      <HDim x1={cx - dx} x2={cx + dx} y={apexY + dy + 35} label={`λ/2 = ${length_mm} mm`} above={false} />
      <text x={cx + 8} y={(apexY + apexY + dy) / 2} fill="#8b949e" fontSize="10">{apex_angle_deg}°</text>
    </DiagramSVG>
  );
}
