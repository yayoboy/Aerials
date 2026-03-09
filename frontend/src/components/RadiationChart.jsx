import { useState } from 'react';
import Plot from 'react-plotly.js';

// dB range shown on polar chart: inner edge = DB_MIN dB, outer edge = 0 dB
const DB_MIN = -30;
const DB_RANGE = -DB_MIN; // 30

// Map dB value to plot radius (clips values below DB_MIN to inner edge)
const toR = db => Math.max(0, DB_RANGE + Math.max(db, DB_MIN));

export default function RadiationChart({ results, loading }) {
  const [showAzimuth, setShowAzimuth] = useState(false);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <div className="spinner" />
    </div>
  );

  if (!results?.results) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <p style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>
          Avvia la simulazione per vedere il diagramma di irradiazione.
        </p>
      </div>
    );
  }

  const rad = results?.results?.radiation;

  if (!rad) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <p style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>
          Dati di irradiazione non disponibili per questa antenna.
        </p>
      </div>
    );
  }

  const thetaDeg = rad.theta_deg;    // elevation 0..180
  const phiDeg   = rad.phi_deg;      // azimuth 0..360
  const eNormDb  = rad.e_norm_db;    // [n_theta][n_phi], max = 0 dB

  // --- Elevation cuts ---
  const iPhi0  = phiDeg.reduce((b, v, i) => Math.abs(v - 0)  < Math.abs(phiDeg[b] - 0)  ? i : b, 0);
  const iPhi90 = phiDeg.reduce((b, v, i) => Math.abs(v - 90) < Math.abs(phiDeg[b] - 90) ? i : b, 0);
  const e0  = thetaDeg.map((_, it) => eNormDb[it][iPhi0]);
  const e90 = thetaDeg.map((_, it) => eNormDb[it][iPhi90]);

  // Mirror 0..180 → full 0..360 circle
  const tFull   = [...thetaDeg, ...thetaDeg.map(t => 360 - t)];
  const e0Full  = [...e0,  ...[...e0].reverse()];
  const e90Full = [...e90, ...[...e90].reverse()];

  // --- Azimuth cut at θ ≈ 90° (horizontal plane) ---
  const iTheta90 = thetaDeg.reduce((b, v, i) => Math.abs(v - 90) < Math.abs(thetaDeg[b] - 90) ? i : b, 0);
  const azimuth  = phiDeg.map((_, ip) => eNormDb[iTheta90][ip]);

  const traceE = {
    type: 'scatterpolar',
    mode: 'lines',
    r: e0Full.map(toR),
    theta: tFull,
    name: 'Piano E (φ=0°)',
    fill: 'toself',
    fillcolor: 'rgba(47,129,247,0.08)',
    line: { color: '#2f81f7', width: 2 },
  };

  const traceH = {
    type: 'scatterpolar',
    mode: 'lines',
    r: e90Full.map(toR),
    theta: tFull,
    name: 'Piano H (φ=90°)',
    fill: 'toself',
    fillcolor: 'rgba(63,185,80,0.08)',
    line: { color: '#3fb950', width: 2, dash: 'dot' },
  };

  const traceAz = {
    type: 'scatterpolar',
    mode: 'lines',
    r: azimuth.map(toR),
    theta: phiDeg,
    name: 'Azimut (θ=90°)',
    fill: 'toself',
    fillcolor: 'rgba(247,129,47,0.08)',
    line: { color: '#f78166', width: 2, dash: 'dash' },
  };

  const data = showAzimuth ? [traceE, traceH, traceAz] : [traceE, traceH];

  const layout = {
    autosize: true,
    paper_bgcolor: 'transparent',
    plot_bgcolor:  'transparent',
    font: { color: '#8b949e', family: 'Inter', size: 11 },
    polar: {
      bgcolor: 'transparent',
      radialaxis: {
        visible: true,
        range: [0, DB_RANGE],
        tickvals: [0, DB_RANGE / 3, (DB_RANGE * 2) / 3, DB_RANGE],
        ticktext: [`${DB_MIN} dB`, `${(DB_MIN * 2) / 3} dB`, `${DB_MIN / 3} dB`, '0 dB'],
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
    margin: { t: 36, r: 40, b: 44, l: 40 },
    legend: {
      font: { color: '#8b949e', size: 11 },
      bgcolor: 'transparent',
      orientation: 'h',
      y: -0.08,
    },
    annotations: [{
      xref: 'paper', yref: 'paper',
      x: 0.5, y: 1.04,
      text: `Direttività massima: <b>${rad.directivity_dbi.toFixed(1)} dBi</b> @ ${rad.frequency_mhz.toFixed(1)} MHz`,
      showarrow: false,
      font: { size: 11, color: '#e6edf3' },
      xanchor: 'center',
    }],
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '4px 8px 0' }}>
        <button
          onClick={() => setShowAzimuth(v => !v)}
          style={{
            background: showAzimuth ? 'rgba(247,129,47,0.15)' : 'transparent',
            border: `1px solid ${showAzimuth ? '#f78166' : 'rgba(240,246,252,0.15)'}`,
            borderRadius: '6px',
            color: showAzimuth ? '#f78166' : '#6e7681',
            cursor: 'pointer',
            fontSize: '11px',
            padding: '2px 10px',
            transition: 'all 0.15s',
          }}
        >
          {showAzimuth ? '✕ Nascondi azimut' : '+ Mostra azimut (θ=90°)'}
        </button>
      </div>

      <Plot
        data={data}
        layout={layout}
        useResizeHandler
        style={{ width: '100%', flex: 1 }}
        config={{ displayModeBar: false }}
      />
    </div>
  );
}
