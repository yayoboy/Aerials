import { DiagramSVG, VWire, HWire, HDim, VDim, FeedDot } from './utils.jsx';

export function buildDiagram(params) {
  const { length_mm = 237, groundplane_mm = 300, frequency_mhz = 300 } = params;
  const lam = Math.round(299792.458 / frequency_mhz);
  const cx = 260, baseY = 150;
  const scaleV = Math.min(100 / length_mm, 0.5);
  const scaleH = Math.min(180 / groundplane_mm, 0.5);
  const mLen = length_mm * scaleV;
  const gpHalf = groundplane_mm / 2 * scaleH;

  return (
    <DiagramSVG>
      <HWire x1={cx - gpHalf} x2={cx + gpHalf} y={baseY} />
      <VWire x={cx} y1={baseY - mLen} y2={baseY} />
      <FeedDot x={cx} y={baseY} />
      <VDim x={cx - 18} y1={baseY - mLen} y2={baseY} label={`λ/4 = ${length_mm} mm`} />
      <HDim x1={cx - gpHalf} x2={cx + gpHalf} y={baseY + 30} label={`⌀ ${groundplane_mm} mm`} above={false} />
    </DiagramSVG>
  );
}
