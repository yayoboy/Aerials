import { DiagramSVG, HWire, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { length_mm = 475, frequency_mhz = 300 } = params;
  const lam = Math.round(299792.458 / frequency_mhz);
  const cx = 260, wireY = 120;
  const scale = 400 / length_mm;
  const half = length_mm / 2 * scale;
  const gap = 5;

  return (
    <DiagramSVG>
      <HWire x1={cx - half} x2={cx - gap} y={wireY} />
      <HWire x1={cx + gap} x2={cx + half} y={wireY} />
      <FeedDot x={cx} y={wireY} />
      <HDim x1={cx - half} x2={cx - gap} y={wireY - 28} label={`${(length_mm/2).toFixed(0)} mm`} />
      <HDim x1={cx + gap} x2={cx + half} y={wireY - 28} label={`${(length_mm/2).toFixed(0)} mm`} />
      <HDim x1={cx - half} x2={cx + half} y={wireY + 35} label={`λ/2 = ${length_mm} mm  (λ=${lam} mm)`} above={false} />
    </DiagramSVG>
  );
}
