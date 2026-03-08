import { DiagramSVG, HWire, VWire, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { length_mm = 1020, frequency_mhz = 144 } = params;
  const lam = Math.round(299792.458 / frequency_mhz);
  const cx = 260, cy = 110;
  const scale = 400 / length_mm;
  const half = length_mm / 2 * scale;
  const h = 30, gap = 6;

  return (
    <DiagramSVG>
      <HWire x1={cx - half} x2={cx + half} y={cy - h/2} />
      <HWire x1={cx - half} x2={cx - gap} y={cy + h/2} />
      <HWire x1={cx + gap} x2={cx + half} y={cy + h/2} />
      <VWire x={cx - half} y1={cy - h/2} y2={cy + h/2} />
      <VWire x={cx + half} y1={cy - h/2} y2={cy + h/2} />
      <FeedDot x={cx} y={cy + h/2} />
      <HDim x1={cx - half} x2={cx + half} y={cy - h/2 - 22} label={`λ/2 = ${length_mm} mm`} />
      <HDim x1={cx - gap} x2={cx + gap} y={cy + h/2 + 28} label={`gap feed`} above={false} />
    </DiagramSVG>
  );
}
