// frontend/src/components/AntennaForm.jsx
import { ANTENNA_MAP } from '../antennas/configs/index.js';

export default function AntennaForm({ antennaType, params, onChange }) {
  const cfg = ANTENNA_MAP[antennaType];
  if (!cfg) return null;

  const set = (name, value) => onChange({ ...params, [name]: value });

  return (
    <div className="antenna-form">
      {cfg.fields.map(field => (
        <div key={field.name} className="form-group">
          <label>{field.label}</label>
          {field.type === 'select' ? (
            <select className="form-input"
                    value={params[field.name] ?? field.options?.[0]?.value ?? ''}
                    onChange={e => set(field.name, e.target.value)}>
              {(field.options || []).map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          ) : field.type === 'number' ? (
            <div className="slider-row">
              <input
                type="range"
                className="param-slider"
                min={field.min ?? 1}
                max={field.max ?? 9999}
                step={field.step ?? 1}
                value={typeof params[field.name] === 'number' ? params[field.name] : (field.min ?? 1)}
                onChange={e => set(field.name, parseFloat(e.target.value))}
              />
              <input
                type="number"
                className="form-input slider-number"
                min={field.min}
                max={field.max}
                step={field.step}
                value={params[field.name] ?? ''}
                onChange={e => {
                  if (e.target.value === '') { set(field.name, ''); return; }
                  const v = parseFloat(e.target.value);
                  if (isNaN(v)) return;
                  const lo = field.min;
                  const hi = field.max;
                  const clamped = lo != null && v < lo ? lo : hi != null && v > hi ? hi : v;
                  set(field.name, clamped);
                }}
              />
            </div>
          ) : (
            <input
              className="form-input"
              type={field.type}
              value={Array.isArray(params[field.name]) ? params[field.name].join(', ') : (params[field.name] ?? '')}
              onChange={e => {
                if (field.type === 'text' && field.name === 'director_lengths_mm') {
                  // Parse comma-separated numbers to array
                  const arr = e.target.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
                  set(field.name, arr.length > 0 ? arr : [980]);
                } else {
                  set(field.name, e.target.value);
                }
              }}
            />
          )}
        </div>
      ))}
    </div>
  );
}
