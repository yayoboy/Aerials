import { DiagramSVG, VWire, HWire, VDim, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { long_element_mm = 1000, stub_length_mm = 330, stub_spacing_mm = 25, frequency_mhz = 146 } = params;
  const scale = Math.min(150 / long_element_mm, 0.2);
  const lH = long_element_mm * scale;
  const sH = stub_length_mm * scale;
  const sp = Math.max(stub_spacing_mm * scale * 3, 20);
  const cx = 260, baseY = 180;

  return (
    <DiagramSVG>
      <VWire x={cx + sp/2} y1={baseY - lH} y2={baseY} />
      <VWire x={cx - sp/2} y1={baseY - sH} y2={baseY} />
      <HWire x1={cx - sp/2} x2={cx + sp/2} y={baseY} />
      <FeedDot x={cx} y={baseY - sH} label="feed (stub top)" />
      <VDim x={cx + sp/2 + 20} y1={baseY - lH} y2={baseY} label={`3λ/4 = ${long_element_mm} mm`} left={false} />
      <VDim x={cx - sp/2 - 20} y1={baseY - sH} y2={baseY} label={`λ/4 = ${stub_length_mm} mm`} />
      <HDim x1={cx - sp/2} x2={cx + sp/2} y={baseY + 25} label={`${stub_spacing_mm} mm`} above={false} />
    </DiagramSVG>
  );
}
