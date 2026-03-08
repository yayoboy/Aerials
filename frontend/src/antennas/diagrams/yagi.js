import { DiagramSVG, HWire, VWire, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const {
    driven_length_mm = 1020, reflector_length_mm = 1050,
    director_lengths_mm = [980, 960], element_spacing_mm = 300,
  } = params;
  const dirs = Array.isArray(director_lengths_mm) ? director_lengths_mm : [director_lengths_mm];
  const allLengths = [reflector_length_mm, driven_length_mm, ...dirs];
  const maxLen = Math.max(...allLengths);
  const scaleH = 420 / maxLen;
  const totalElements = 2 + dirs.length;
  const scaleV = Math.min(160 / ((totalElements) * element_spacing_mm * scaleH * 0.6), 1);
  const spY = Math.min(element_spacing_mm * scaleH * scaleV, 45);
  const cx = 260;
  const startY = 30;
  const gap = 5;

  const rows = [
    { len: reflector_length_mm, y: startY, label: `Riflettore ${reflector_length_mm} mm`, isFed: false },
    { len: driven_length_mm,    y: startY + spY, label: `Dipolo ${driven_length_mm} mm`, isFed: true },
    ...dirs.map((d, i) => ({
      len: d, y: startY + spY * (2 + i),
      label: `Dir.${i+1} ${d} mm`, isFed: false,
    })),
  ];

  return (
    <DiagramSVG>
      {rows.map((r, i) => {
        const half = r.len / 2 * scaleH;
        return (
          <g key={i}>
            {r.isFed ? (
              <>
                <HWire x1={cx - half} x2={cx - gap} y={r.y} />
                <HWire x1={cx + gap} x2={cx + half} y={r.y} />
                <FeedDot x={cx} y={r.y} />
              </>
            ) : (
              <HWire x1={cx - half} x2={cx + half} y={r.y} />
            )}
            <text x={cx + half + 8} y={r.y + 4} fill="#8b949e" fontSize="10">{r.label}</text>
          </g>
        );
      })}
      <VWire x={cx} y1={startY} y2={rows[rows.length-1].y} thick={1.5} />
      {rows.length >= 2 && (
        <VDim x={cx - 22} y1={rows[0].y} y2={rows[1].y} label={`${element_spacing_mm} mm`} />
      )}
    </DiagramSVG>
  );
}
