import React, { useState } from 'react';
import Plot from 'react-plotly.js';

function App() {
  const [params, setParams] = useState({
    frequency_mhz: 300,
    length_mm: 475,
    radius_mm: 1.0
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/simulate/dipole', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Simulation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleParamChange = (e) => {
    setParams({
      ...params,
      [e.target.name]: parseFloat(e.target.value) || 0
    });
  };

  return (
    <div className="app-container">
      {/* Sidebar Controls */}
      <aside className="sidebar">
        <h1>
          <span className="icon">⚡</span>
          OpenEMS Web
        </h1>

        <div className="form-group">
          <label>Antenna Type</label>
          <select className="form-input" disabled>
            <option>Half-Wave Dipole</option>
          </select>
        </div>

        <div className="form-group">
          <label>Frequency (MHz)</label>
          <input
            className="form-input"
            type="number"
            name="frequency_mhz"
            value={params.frequency_mhz}
            onChange={handleParamChange}
          />
        </div>

        <div className="form-group">
          <label>Length (mm)</label>
          <input
            className="form-input"
            type="number"
            name="length_mm"
            value={params.length_mm}
            onChange={handleParamChange}
          />
        </div>

        <div className="form-group">
          <label>Wire Radius (mm)</label>
          <input
            className="form-input"
            type="number"
            name="radius_mm"
            value={params.radius_mm}
            onChange={handleParamChange}
          />
        </div>

        <button
          className="btn-primary"
          onClick={handleSimulate}
          disabled={loading}
        >
          {loading ? 'Simulating...' : 'Run FDTD Simulation'}
        </button>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">

        <div className="glass-panel">
          <h2 className="panel-header">Simulation Results: S11 Return Loss</h2>
          <div className="plot-container">
            {loading ? (
              <div className="spinner"></div>
            ) : results && results.results ? (
              <Plot
                data={[
                  {
                    x: results.results.frequencies_mhz,
                    y: results.results.s11_db,
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: '#2f81f7', size: 8 },
                    line: { color: '#2f81f7', width: 3 }
                  }
                ]}
                layout={{
                  autosize: true,
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  font: { color: '#8b949e', family: 'Inter' },
                  xaxis: {
                    title: 'Frequency (MHz)',
                    gridcolor: 'rgba(240, 246, 252, 0.1)',
                    zerolinecolor: 'rgba(240, 246, 252, 0.2)'
                  },
                  yaxis: {
                    title: 'S11 (dB)',
                    gridcolor: 'rgba(240, 246, 252, 0.1)',
                    zerolinecolor: 'rgba(240, 246, 252, 0.2)'
                  },
                  margin: { t: 20, r: 20, l: 60, b: 60 }
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
            ) : (
              <p style={{ color: 'var(--text-secondary)' }}>
                Configure parameters and run the simulation to view results.
              </p>
            )}
          </div>
        </div>

        <div className="glass-panel">
          <h2 className="panel-header">3D View (Coming Soon)</h2>
          <div className="plot-container" style={{ height: '300px' }}>
            <p style={{ color: 'var(--text-secondary)' }}>
              Three.js integration for 3D antenna geometry visualization.
            </p>
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;
