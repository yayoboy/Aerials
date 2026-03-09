import Plot from 'react-plotly.js';

export default function RadiationChart({ results, loading }) {
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <div className="spinner" />
    </div>
  );

  const rad = results?.results?.radiation;

  if (!results?.results) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <p style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>
          Avvia la simulazione per vedere il diagramma di irradiazione.
        </p>
      </div>
    );
  }

  if (!rad) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <p style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>
          Dati di irradiazione non disponibili per questa antenna.
        </p>
      </div>
    );
  }

  const thetaDeg = rad.theta_deg;
  const eNormDb  = rad.e_norm_db;   // shape [n_theta][n_phi]
  const phiDeg   = rad.phi_deg;

  // Find phi indices closest to 0° and 90°
  const iPhi0  = phiDeg.reduce((best, v, i) => Math.abs(v - 0)  < Math.abs(phiDeg[best] - 0)  ? i : best, 0);
  const iPhi90 = phiDeg.reduce((best, v, i) => Math.abs(v - 90) < Math.abs(phiDeg[best] - 90) ? i : best, 0);

  // Extract elevation patterns at phi=0° and phi=90°
  const e0  = thetaDeg.map((_, it) => eNormDb[it][iPhi0]);
  const e90 = thetaDeg.map((_, it) => eNormDb[it][iPhi90]);

  // Convert to polar: theta in degrees, r in linear (0..1 from dB)
  // Plotly scatterpolar: theta = azimuth around circle, r = radius
  // We map elevation theta (0=up, 180=down) to polar angles
  // Show both halves: theta 0..180 and mirror 180..360
  const tFull  = [...thetaDeg, ...thetaDeg.map(t => 360 - t)];
  const e0Full = [...e0,  ...[...e0].reverse()];
  const e90Full= [...e90, ...[...e90].reverse()];

  // Convert dB to linear (0..1)
  const toLinear = db => Math.max(0, Math.pow(10, db / 20));

  const trace0 = {
    type: 'scatterpolar',
    mode: 'lines',
    r: e0Full.map(toLinear),
    theta: tFull,
    name: 'φ = 0° (E-plane)',
    line: { color: '#2f81f7', width: 2 },
  };

  const trace90 = {
    type: 'scatterpolar',
    mode: 'lines',
    r: e90Full.map(toLinear),
    theta: tFull,
    name: 'φ = 90° (H-plane)',
    line: { color: '#3fb950', width: 2, dash: 'dot' },
  };

  const layout = {
    autosize: true,
    paper_bgcolor: 'transparent',
    plot_bgcolor:  'transparent',
    font: { color: '#8b949e', family: 'Inter', size: 11 },
    polar: {
      bgcolor: 'transparent',
      radialaxis: {
        visible: true,
        range: [0, 1],
        tickvals: [0.25, 0.5, 0.75, 1],
        ticktext: ['−12 dB', '−6 dB', '−2.5 dB', '0 dB'],
        gridcolor: 'rgba(240,246,252,0.12)',
        linecolor: 'rgba(240,246,252,0.15)',
        tickfont: { size: 9, color: '#6e7681' },
        showticklabels: true,
      },
      angularaxis: {
        tickmode: 'array',
        tickvals: [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
        ticktext: ['0°','30°','60°','90°','120°','150°','180°','210°','240°','270°','300°','330°'],
        gridcolor: 'rgba(240,246,252,0.12)',
        linecolor: 'rgba(240,246,252,0.15)',
        tickfont: { size: 9, color: '#6e7681' },
        direction: 'clockwise',
        rotation: 90,
      },
    },
    margin: { t: 30, r: 40, b: 30, l: 40 },
    legend: {
      font: { color: '#8b949e', size: 11 },
      bgcolor: 'transparent',
      orientation: 'h',
      y: -0.05,
    },
    annotations: [{
      xref: 'paper', yref: 'paper',
      x: 0.5, y: 1.02,
      text: `Direttività massima: <b>${rad.directivity_dbi.toFixed(1)} dBi</b> @ ${rad.frequency_mhz.toFixed(1)} MHz`,
      showarrow: false,
      font: { size: 11, color: '#e6edf3' },
      xanchor: 'center',
    }],
  };

  return (
    <Plot
      data={[trace0, trace90]}
      layout={layout}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ displayModeBar: false }}
    />
  );
}
