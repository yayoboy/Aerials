// frontend/src/App.jsx
import { useState } from 'react';
import './App.css';
import AntennaSelector from './components/AntennaSelector.jsx';
import AntennaForm     from './components/AntennaForm.jsx';
import ConductorForm   from './components/ConductorForm.jsx';
import S11Chart        from './components/S11Chart.jsx';
import Antenna3DView   from './components/Antenna3DView.jsx';
import AntennaSpecs    from './components/AntennaSpecs.jsx';
import SimHistory      from './components/SimHistory.jsx';
import AntennaDiagram  from './components/AntennaDiagram.jsx';
import GlossaryPanel   from './components/GlossaryPanel.jsx';
import Glossary        from './components/Glossary.jsx';
import RadiationChart  from './components/RadiationChart.jsx';
import { ANTENNA_MAP } from './antennas/configs/index.js';

const HISTORY_KEY = 'aerials_history';
const MAX_HISTORY = 10;

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]'); }
  catch { return []; }
}

function saveHistory(entries) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
  } catch {
    // localStorage quota exceeded — silently skip persistence
  }
}

const DEFAULT_CONDUCTOR = {
  material: 'copper',
  cross_section: 'round',
  radius_mm: 1.0,
};

export default function App() {
  const [antennaType, setAntennaType] = useState('dipole');
  const [params,      setParams]      = useState(ANTENNA_MAP['dipole'].defaultParams);
  const [conductor,   setConductor]   = useState(DEFAULT_CONDUCTOR);
  const [loading,     setLoading]     = useState(false);
  const [results,     setResults]     = useState(null);
  const [error,       setError]       = useState(null);
  const [history,     setHistory]     = useState(loadHistory);
  const [activeTab,   setActiveTab]   = useState('3d');

  const handleAntennaChange = (type) => {
    setAntennaType(type);
    setParams(ANTENNA_MAP[type].defaultParams);
    setResults(null);
    setError(null);
  };

  const handleSimulate = async () => {
    setLoading(true);
    setResults(null);
    setError(null);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 360_000);
    try {
      const res = await fetch(`/api/simulate/${antennaType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          antenna_params: params,
          conductor,
          with_radiation: true,
        }),
        signal: controller.signal,
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? 'Simulation failed');
      } else {
        setResults(data);
        const s11 = data.results.s11_db;
        const freqs = data.results.frequencies_mhz;
        const minIdx = s11.indexOf(Math.min(...s11));
        const label = ANTENNA_MAP[antennaType]?.label ?? antennaType;
        const entry = {
          id: Date.now(),
          antenna_type: antennaType,
          label,
          params: { ...params },
          conductor: { ...conductor },
          results: data,
          resonance_mhz: freqs[minIdx],
          min_s11_db: s11[minIdx],
        };
        const updated = [entry, ...history].slice(0, MAX_HISTORY);
        setHistory(updated);
        saveHistory(updated);
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Simulazione interrotta: timeout di 120 secondi superato.');
      } else {
        setError(err.message);
      }
    } finally {
      clearTimeout(timeout);
      setLoading(false);
    }
  };

  const handleRestoreHistory = (entry) => {
    if (loading) return;
    setAntennaType(entry.antenna_type);
    setParams(entry.params);
    setConductor(entry.conductor);
    setResults(entry.results);
    setError(null);
  };

  const handleDeleteHistory = (id) => {
    const updated = history.filter(h => h.id !== id);
    setHistory(updated);
    saveHistory(updated);
  };

  const cfg = ANTENNA_MAP[antennaType];

  return (
    <div className="app-container">
      <aside className="sidebar">
        <h1><span className="icon">⚡</span>Aerials</h1>

        <div className="form-group">
          <label>Tipo di Antenna</label>
          <AntennaSelector selected={antennaType} onChange={handleAntennaChange} />
        </div>

        <AntennaForm
          antennaType={antennaType}
          params={params}
          onChange={setParams}
        />

        <ConductorForm
          conductor={conductor}
          onChange={setConductor}
        />

        <button
          className="btn-primary"
          onClick={handleSimulate}
          disabled={loading}
        >
          {loading ? 'Simulazione in corso...' : 'Avvia simulazione FDTD'}
        </button>

        {error && (
          <p style={{ color: '#f85149', marginTop: '8px', fontSize: '13px' }}>
            Errore: {error}
          </p>
        )}

        <SimHistory
          history={history}
          onRestore={handleRestoreHistory}
          onDelete={handleDeleteHistory}
          disabled={loading}
        />
      </aside>

      <main className="main-content">
        <div className="glass-panel panel-3d">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0' }}>
            <h2 className="panel-header" style={{ marginBottom: 0, borderBottom: 'none', paddingBottom: 0 }}>
              {activeTab === '3d' ? `Vista 3D — ${cfg?.label ?? antennaType}` : `Irradiazione — ${cfg?.label ?? antennaType}`}
            </h2>
            <div className="panel-tabs" style={{ marginBottom: 0, borderBottom: 'none', paddingBottom: 0 }}>
              <button className={`panel-tab${activeTab === '3d' ? ' active' : ''}`} onClick={() => setActiveTab('3d')}>Vista 3D</button>
              <button className={`panel-tab${activeTab === 'radiation' ? ' active' : ''}`} onClick={() => setActiveTab('radiation')}>Irradiazione</button>
            </div>
          </div>
          <div style={{ height: '1px', background: 'var(--panel-border)', margin: '10px 0 14px' }} />

          {activeTab === '3d' ? (
            <>
              <div className="plot-container" style={{ height: '300px' }}>
                <Antenna3DView
                  antennaType={antennaType}
                  params={params}
                  conductor={conductor}
                />
              </div>
              <AntennaSpecs
                antennaType={antennaType}
                params={params}
                conductor={conductor}
              />
            </>
          ) : (
            <div style={{ flex: 1, minHeight: 0 }}>
              <RadiationChart results={results} loading={loading} />
            </div>
          )}
        </div>

        <div className="glass-panel panel-chart">
          <h2 className="panel-header"><Glossary term="S11">S11</Glossary> Return Loss</h2>
          <div style={{ flex: 1, minHeight: 0 }}>
            <S11Chart results={results} loading={loading} />
          </div>
        </div>

        <div className="glass-panel panel-diagram">
          <h2 className="panel-header">
            Diagramma costruttivo — {cfg?.label ?? antennaType}
          </h2>
          <div style={{ flex: 1, minHeight: 0 }}>
            <AntennaDiagram antennaType={antennaType} params={params} />
          </div>
        </div>

        <GlossaryPanel />
      </main>
    </div>
  );
}
