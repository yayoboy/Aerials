import { DiagramSVG, HWire, VWire, HDim, VDim, FeedDot } from './utils.jsx';

export function buildDiagram(params) {
  const { element_length_mm = 990, tail_length_mm = 171, feed_gap_mm = 27, frequency_mhz = 144 } = params;
  const lam = 299792.458 / frequency_mhz;
  const D = Math.max(lam * 0.005, 1);
  const totalDepth = tail_length_mm * 2 + D + feed_gap_mm;

  const scaleH = Math.min(380 / element_length_mm, 0.45);
  const scaleV = Math.min(150 / totalDepth, 0.8);
  const A = element_length_mm * scaleH;
  const B = tail_length_mm * scaleV;
  const C = Math.max(feed_gap_mm * scaleH, 6);
  const Ds = D * scaleV;
  const DsVis = Math.max(Ds, 15);
  const depth = B + DsVis + B;

  const cx = 260, topY = 35;
  const gap = C / 2;

  return (
    <DiagramSVG>
      <HWire x1={cx - A/2} x2={cx - gap} y={topY} />
      <HWire x1={cx + gap} x2={cx + A/2} y={topY} />
      <VWire x={cx - A/2} y1={topY} y2={topY + B} />
      <VWire x={cx + A/2} y1={topY} y2={topY + B} />
      <HWire x1={cx - A/2} x2={cx + A/2} y={topY + depth} />
      <VWire x={cx - A/2} y1={topY + depth - B} y2={topY + depth} />
      <VWire x={cx + A/2} y1={topY + depth - B} y2={topY + depth} />
      <FeedDot x={cx} y={topY} />
      <HDim x1={cx - A/2} x2={cx + A/2} y={topY - 18} label={`A = ${element_length_mm} mm`} />
      <VDim x={cx + A/2 + 22} y1={topY} y2={topY + B} label={`B = ${tail_length_mm} mm`} left={false} />
      <VDim x={cx - A/2 - 22} y1={topY + B} y2={topY + B + DsVis} label={`D = ${Math.round(D)} mm`} />
      <HDim x1={cx - gap} x2={cx + gap} y={topY + 18} label={`C = ${feed_gap_mm} mm`} above={false} />
    </DiagramSVG>
  );
}
