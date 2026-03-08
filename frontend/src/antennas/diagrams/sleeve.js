import { DiagramSVG, VWire, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { monopole_length_mm = 490, sleeve_length_mm = 245, frequency_mhz = 144 } = params;
  const cx = 260, baseY = 170;
  const totalH = monopole_length_mm + sleeve_length_mm;
  const scale = Math.min(140 / totalH, 0.5);
  const mH = monopole_length_mm * scale;
  const sH = sleeve_length_mm * scale;
  const sleeveW = 14;

  return (
    <DiagramSVG>
      <rect x={cx - sleeveW/2} y={baseY - sH} width={sleeveW} height={sH}
        fill="none" stroke="#58a6ff" strokeWidth="2.5" />
      <VWire x={cx} y1={baseY - mH} y2={baseY} />
      <FeedDot x={cx} y={baseY} />
      <VDim x={cx + sleeveW/2 + 18} y1={baseY - sH} y2={baseY} label={`λ/8 = ${sleeve_length_mm} mm`} left={false} />
      <VDim x={cx - sleeveW/2 - 18} y1={baseY - mH} y2={baseY} label={`λ/4 = ${monopole_length_mm} mm`} />
    </DiagramSVG>
  );
}
