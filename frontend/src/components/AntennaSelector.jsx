// frontend/src/components/AntennaSelector.jsx
import { ANTENNA_CONFIGS } from '../antennas/configs/index.js';

export default function AntennaSelector({ selected, onChange }) {
  return (
    <div className="antenna-selector">
      {ANTENNA_CONFIGS.map(cfg => (
        <button
          key={cfg.id}
          className={`antenna-card ${selected === cfg.id ? 'active' : ''}`}
          onClick={() => onChange(cfg.id)}
          title={cfg.description}
        >
          <span className="antenna-card-label">{cfg.label}</span>
        </button>
      ))}
    </div>
  );
}
