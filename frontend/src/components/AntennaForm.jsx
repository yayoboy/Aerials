// frontend/src/components/AntennaForm.jsx
import { useState, useEffect } from 'react';
import { ANTENNA_MAP } from '../antennas/configs/index.js';

export default function AntennaForm({ antennaType, params, onChange }) {
  const cfg = ANTENNA_MAP[antennaType];
  const [drafts, setDrafts] = useState({});

  useEffect(() => { setDrafts({}); }, [antennaType]);

  if (!cfg) return null;

  const clampToField = (key, val) => {
    const field = cfg.fields.find(f => f.name === key);
    if (!field || typeof val !== 'number') return val;
    const lo = field.min, hi = field.max;
    return lo != null && val < lo ? lo : hi != null && val > hi ? hi : val;
  };

  const set = (name, value) => {
    const updated = { ...params, [name]: value };
    if (name === 'frequency_mhz' && typeof cfg.derivedFromFreq === 'function') {
      const derived = cfg.derivedFromFreq(value, params);
      const clampedDerived = Object.fromEntries(
        Object.entries(derived).map(([k, v]) => [k, clampToField(k, v)])
      );
      onChange({ ...updated, ...clampedDerived });
    } else {
      onChange(updated);
    }
  };

  const commitNumber = (name, rawValue) => {
    setDrafts(d => { const nd = { ...d }; delete nd[name]; return nd; });
    if (rawValue === '' || rawValue == null) return;
    const v = parseFloat(rawValue);
    if (isNaN(v)) return;
    const field = cfg.fields.find(f => f.name === name);
    const lo = field?.min, hi = field?.max;
    const clamped = lo != null && v < lo ? lo : hi != null && v > hi ? hi : v;
    set(name, clamped);
  };

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
                value={field.name in drafts ? drafts[field.name] : (params[field.name] ?? '')}
                onChange={e => setDrafts(d => ({ ...d, [field.name]: e.target.value }))}
                onBlur={e => commitNumber(field.name, e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') commitNumber(field.name, e.target.value); }}
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
