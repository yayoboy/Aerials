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
          ) : (
            <input
              className="form-input"
              type={field.type}
              min={field.min}
              max={field.max}
              step={field.step}
              value={Array.isArray(params[field.name]) ? params[field.name].join(', ') : (params[field.name] ?? '')}
              onChange={e => {
                if (field.type === 'number') {
                  set(field.name, e.target.value === '' ? '' : parseFloat(e.target.value));
                } else if (field.type === 'text' && field.name === 'director_lengths_mm') {
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
