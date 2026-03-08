import { ANTENNA_MAP } from '../antennas/configs/index.js';
import { MATERIALS, CROSS_SECTIONS } from '../constants/conductors.js';
import Glossary from './Glossary.jsx';

function fmt(value) {
  if (Array.isArray(value)) return value.join(', ') + ' mm';
  if (typeof value === 'number') return value % 1 === 0 ? String(value) : value.toFixed(1);
  return String(value ?? '—');
}

export default function AntennaSpecs({ antennaType, params, conductor }) {
  const cfg = ANTENNA_MAP[antennaType];
  if (!cfg) return null;

  const freqMhz = params.frequency_mhz;
  const lambdaMm = freqMhz > 0 ? Math.round(299792.458 / freqMhz) : null;

  const material = MATERIALS.find(m => m.id === conductor?.material);
  const section  = CROSS_SECTIONS.find(s => s.id === conductor?.cross_section);

  const conductorDims = section?.fields.map(f => {
    const labels = {
      radius_mm: 'Raggio', outer_diameter_mm: 'Ø est.', wall_thickness_mm: 'Spessore',
      width_mm: 'Larghezza', thickness_mm: 'Spessore',
    };
    return { label: labels[f] ?? f, value: `${conductor?.[f] ?? '—'} mm` };
  }) ?? [];

  return (
    <div className="antenna-specs">
      <div className="specs-section">
        <span className="specs-title">Geometria</span>
        <div className="specs-grid">
          {cfg.fields.map(field => {
            if (field.name === 'frequency_mhz') return null;
            const raw = params[field.name];
            const label = field.label.replace(/ \(mm\)| \(mm, virgola\)/, '');
            return (
              <div key={field.name} className="spec-row">
                <span className="spec-label">{label}</span>
                <span className="spec-value">
                  {Array.isArray(raw) ? raw.join(', ') + ' mm' : fmt(raw) + (field.type === 'number' ? ' mm' : '')}
                </span>
              </div>
            );
          })}
          {freqMhz != null && (
            <div className="spec-row">
              <span className="spec-label">Frequenza</span>
              <span className="spec-value">{fmt(freqMhz)} MHz</span>
            </div>
          )}
          {lambdaMm != null && (
            <div className="spec-row">
              <span className="spec-label">Lunghezza d'onda</span>
              <span className="spec-value"><Glossary term="λ">λ</Glossary> = {lambdaMm} mm</span>
            </div>
          )}
        </div>
      </div>

      <div className="specs-section">
        <span className="specs-title">Conduttore</span>
        <div className="specs-grid">
          <div className="spec-row">
            <span className="spec-label">Materiale</span>
            <span className="spec-value">{material?.label ?? '—'}</span>
          </div>
          <div className="spec-row">
            <span className="spec-label">Sezione</span>
            <span className="spec-value">{section?.label ?? '—'}</span>
          </div>
          {conductorDims.map(d => (
            <div key={d.label} className="spec-row">
              <span className="spec-label">{d.label}</span>
              <span className="spec-value">{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
