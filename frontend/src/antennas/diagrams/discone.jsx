import { DiagramSVG, HDim, VDim, FeedDot } from './utils.jsx';

export function buildDiagram(params) {
  const { cone_length_mm = 185, cone_angle_deg = 60, disc_diameter_mm = 150, frequency_mhz = 400 } = params;
  const cx = 260, apexY = 80;
  const scaleC = Math.min(120 / cone_length_mm, 0.6);
  const discScale = Math.min(100 / disc_diameter_mm, 0.5);
  const coneH = cone_length_mm * scaleC;
  const halfAngle = (cone_angle_deg / 2) * Math.PI / 180;
  const coneBase = Math.tan(halfAngle) * coneH;
  const discR = disc_diameter_mm / 2 * discScale;

  return (
    <DiagramSVG>
      <ellipse cx={cx} cy={apexY - 10} rx={discR} ry={discR * 0.3} fill="none" stroke="#58a6ff" strokeWidth="2.5" />
      <line x1={cx} y1={apexY} x2={cx - coneBase} y2={apexY + coneH} stroke="#58a6ff" strokeWidth="2.5" />
      <line x1={cx} y1={apexY} x2={cx + coneBase} y2={apexY + coneH} stroke="#58a6ff" strokeWidth="2.5" />
      <FeedDot x={cx} y={apexY} />
      <HDim x1={cx - discR} x2={cx + discR} y={apexY - 10 - 22} label={`⌀ disc ${disc_diameter_mm} mm`} />
      <VDim x={cx + coneBase + 18} y1={apexY} y2={apexY + coneH} label={`λ/4 = ${cone_length_mm} mm`} left={false} />
      <text x={cx + 18} y={apexY + coneH * 0.4} fill="#8b949e" fontSize="10">{cone_angle_deg}°</text>
    </DiagramSVG>
  );
}
