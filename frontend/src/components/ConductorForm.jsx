// frontend/src/components/ConductorForm.jsx
import { MATERIALS, CROSS_SECTIONS } from '../constants/conductors.js';

export default function ConductorForm({ conductor, onChange }) {
  const section = CROSS_SECTIONS.find(s => s.id === conductor.cross_section) || CROSS_SECTIONS[0];
  const set = (key, value) => onChange({ ...conductor, [key]: value });

  const FIELD_LABELS = {
    radius_mm:         'Raggio (mm)',
    outer_diameter_mm: 'Diametro esterno (mm)',
    wall_thickness_mm: 'Spessore parete (mm)',
    width_mm:          'Larghezza (mm)',
    thickness_mm:      'Spessore (mm)',
  };

  return (
    <div className="conductor-form">
      <h3 className="section-title">Conduttore</h3>

      <div className="form-group">
        <label>Materiale</label>
        <select className="form-input" value={conductor.material}
                onChange={e => set('material', e.target.value)}>
          {MATERIALS.map(m => (
            <option key={m.id} value={m.id}>{m.label}</option>
          ))}
        </select>
      </div>

      {conductor.material === 'custom' && (
        <div className="form-group">
          <label>Conduttività (S/m)</label>
          <input className="form-input" type="number" min="0" step="1e6"
                 value={conductor.conductivity ?? ''}
                 onChange={e => set('conductivity', parseFloat(e.target.value))} />
        </div>
      )}

      <div className="form-group">
        <label>Sezione trasversale</label>
        <select className="form-input" value={conductor.cross_section}
                onChange={e => {
                  const sec = CROSS_SECTIONS.find(s => s.id === e.target.value);
                  onChange({ ...conductor, cross_section: e.target.value, ...sec.defaults });
                }}>
          {CROSS_SECTIONS.map(s => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
      </div>

      {section.fields.map(field => (
        <div key={field} className="form-group">
          <label>{FIELD_LABELS[field] ?? field}</label>
          <input className="form-input" type="number" min="0.01" step="0.1"
                 value={conductor[field] ?? ''}
                 onChange={e => set(field, parseFloat(e.target.value))} />
        </div>
      ))}
    </div>
  );
}
