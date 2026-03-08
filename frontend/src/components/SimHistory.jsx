// frontend/src/components/SimHistory.jsx
export default function SimHistory({ history, onRestore, onDelete, disabled }) {
  if (history.length === 0) return null;

  return (
    <div className="sim-history">
      <h3 className="section-title">Storico</h3>
      <ul className="history-list">
        {history.map(entry => (
          <li key={entry.id} className="history-item">
            <button className="history-restore" onClick={() => onRestore(entry)} disabled={disabled}>
              <span className="history-label">{entry.label}</span>
              <span className="history-meta">
                {entry.resonance_mhz?.toFixed(1)} MHz &nbsp;
                {entry.min_s11_db?.toFixed(1)} dB
              </span>
            </button>
            <button
              className="history-delete"
              onClick={() => onDelete(entry.id)}
              title="Rimuovi"
              disabled={disabled}
            >×</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
