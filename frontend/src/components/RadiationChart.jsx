import { useState } from 'react';
import Plot from 'react-plotly.js';

const DB_MIN   = -30;
const DB_RANGE = -DB_MIN; // 30

// dB → plot radius (clips below DB_MIN to 0)
const toR = db => Math.max(0, DB_RANGE + Math.max(db, DB_MIN));

// ---- 3D surface helpers ----
function buildSurface(thetaDeg, phiDeg, eNormDb) {
  const nT = thetaDeg.length;
  const nP = phiDeg.length;
  const X = [], Y = [], Z = [], C = [];

  for (let it = 0; it < nT; it++) {
    const tRad = (thetaDeg[it] * Math.PI) / 180;
    const rowX = [], rowY = [], rowZ = [], rowC = [];
    for (let ip = 0; ip < nP; ip++) {
      const pRad = (phiDeg[ip] * Math.PI) / 180;
      const r    = toR(eNormDb[it][ip]);
      rowX.push(r * Math.sin(tRad) * Math.cos(pRad));
      rowY.push(r * Math.sin(tRad) * Math.sin(pRad));
      rowZ.push(r * Math.cos(tRad));
      rowC.push(Math.max(eNormDb[it][ip], DB_MIN)); // dB for color
    }
    X.push(rowX); Y.push(rowY); Z.push(rowZ); C.push(rowC);
  }
  return { X, Y, Z, C };
}

export default function RadiationChart({ results, loading }) {
  const [mode, setMode]           = useState('2d');   // '2d' | '3d'
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

  const thetaDeg = rad.theta_deg;   // elevation 0..180
  const phiDeg   = rad.phi_deg;     // azimuth 0..360
  const eNormDb  = rad.e_norm_db;   // [n_theta][n_phi], max = 0 dB

  const infoText = `Direttività massima: <b>${rad.directivity_dbi.toFixed(1)} dBi</b> @ ${rad.frequency_mhz.toFixed(1)} MHz`;

  // ---- toolbar ----
  const btnBase = {
    border: '1px solid rgba(240,246,252,0.15)',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '11px',
    padding: '2px 10px',
    transition: 'all 0.15s',
  };

  const toolbar = (
    <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end', padding: '4px 8px 0' }}>
      <button
        onClick={() => setMode('2d')}
        style={{
          ...btnBase,
          background: mode === '2d' ? 'rgba(47,129,247,0.15)' : 'transparent',
          border: `1px solid ${mode === '2d' ? '#2f81f7' : 'rgba(240,246,252,0.15)'}`,
          color: mode === '2d' ? '#2f81f7' : '#6e7681',
        }}
      >
        2D
      </button>
      <button
        onClick={() => setMode('3d')}
        style={{
          ...btnBase,
          background: mode === '3d' ? 'rgba(47,129,247,0.15)' : 'transparent',
          border: `1px solid ${mode === '3d' ? '#2f81f7' : 'rgba(240,246,252,0.15)'}`,
          color: mode === '3d' ? '#2f81f7' : '#6e7681',
        }}
      >
        3D
      </button>
      {mode === '2d' && (
        <button
          onClick={() => setShowAzimuth(v => !v)}
          style={{
            ...btnBase,
            background: showAzimuth ? 'rgba(247,129,47,0.15)' : 'transparent',
            border: `1px solid ${showAzimuth ? '#f78166' : 'rgba(240,246,252,0.15)'}`,
            color: showAzimuth ? '#f78166' : '#6e7681',
          }}
        >
          {showAzimuth ? '✕ Azimut' : '+ Azimut (θ=90°)'}
        </button>
      )}
    </div>
  );

  // ================================================================
  // 3D mode
  // ================================================================
  if (mode === '3d') {
    const { X, Y, Z, C } = buildSurface(thetaDeg, phiDeg, eNormDb);

    const surface = {
      type: 'surface',
      x: X, y: Y, z: Z,
      surfacecolor: C,
      colorscale: [
        [0,   '#0d1117'],
        [0.2, '#1e3a5f'],
        [0.4, '#2f81f7'],
        [0.6, '#3fb950'],
        [0.8, '#f0b232'],
        [1,   '#ff6b6b'],
      ],
      cmin: DB_MIN,
      cmax: 0,
      showscale: true,
      colorbar: {
        title: { text: 'dB', font: { color: '#8b949e', size: 11 } },
        tickfont: { color: '#8b949e', size: 10 },
        thickness: 12,
        len: 0.6,
        tickvals: [DB_MIN, DB_MIN * 2 / 3, DB_MIN / 3, 0],
        ticktext: [`${DB_MIN}`, `${DB_MIN * 2 / 3}`, `${DB_MIN / 3}`, '0 dB'],
        bgcolor: 'transparent',
        outlinecolor: 'rgba(240,246,252,0.15)',
      },
      contours: {
        x: { highlight: false },
        y: { highlight: false },
        z: { highlight: false },
      },
      lighting: { ambient: 0.6, diffuse: 0.8, specular: 0.2, roughness: 0.5 },
      lightposition: { x: 1, y: 1, z: 2 },
      hovertemplate: '%{surfacecolor:.1f} dB<extra></extra>',
    };

    const layout3d = {
      autosize: true,
      paper_bgcolor: 'transparent',
      font: { color: '#8b949e', family: 'Inter', size: 11 },
      margin: { t: 36, r: 20, b: 20, l: 20 },
      scene: {
        bgcolor: 'transparent',
        xaxis: { visible: false, showgrid: false },
        yaxis: { visible: false, showgrid: false },
        zaxis: { visible: false, showgrid: false },
        aspectmode: 'data',
        camera: { eye: { x: 1.4, y: 1.4, z: 0.8 } },
      },
      annotations: [{
        xref: 'paper', yref: 'paper',
        x: 0.5, y: 1.03,
        text: infoText,
        showarrow: false,
        font: { size: 11, color: '#e6edf3' },
        xanchor: 'center',
      }],
    };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {toolbar}
        <Plot
          data={[surface]}
          layout={layout3d}
          useResizeHandler
          style={{ width: '100%', flex: 1 }}
          config={{ displayModeBar: false, scrollZoom: true }}
        />
      </div>
    );
  }

  // ================================================================
  // 2D mode
  // ================================================================
  const iPhi0  = phiDeg.reduce((b, v, i) => Math.abs(v - 0)  < Math.abs(phiDeg[b] - 0)  ? i : b, 0);
  const iPhi90 = phiDeg.reduce((b, v, i) => Math.abs(v - 90) < Math.abs(phiDeg[b] - 90) ? i : b, 0);
  const e0  = thetaDeg.map((_, it) => eNormDb[it][iPhi0]);
  const e90 = thetaDeg.map((_, it) => eNormDb[it][iPhi90]);

  const tFull   = [...thetaDeg, ...thetaDeg.map(t => 360 - t)];
  const e0Full  = [...e0,  ...[...e0].reverse()];
  const e90Full = [...e90, ...[...e90].reverse()];

  const iTheta90 = thetaDeg.reduce((b, v, i) => Math.abs(v - 90) < Math.abs(thetaDeg[b] - 90) ? i : b, 0);
  const azimuth  = phiDeg.map((_, ip) => eNormDb[iTheta90][ip]);

  const traceE = {
    type: 'scatterpolar', mode: 'lines',
    r: e0Full.map(toR), theta: tFull,
    name: 'Piano E (φ=0°)',
    fill: 'toself', fillcolor: 'rgba(47,129,247,0.08)',
    line: { color: '#2f81f7', width: 2 },
  };
  const traceH = {
    type: 'scatterpolar', mode: 'lines',
    r: e90Full.map(toR), theta: tFull,
    name: 'Piano H (φ=90°)',
    fill: 'toself', fillcolor: 'rgba(63,185,80,0.08)',
    line: { color: '#3fb950', width: 2, dash: 'dot' },
  };
  const traceAz = {
    type: 'scatterpolar', mode: 'lines',
    r: azimuth.map(toR), theta: phiDeg,
    name: 'Azimut (θ=90°)',
    fill: 'toself', fillcolor: 'rgba(247,129,47,0.08)',
    line: { color: '#f78166', width: 2, dash: 'dash' },
  };

  const data2d = showAzimuth ? [traceE, traceH, traceAz] : [traceE, traceH];

  const layout2d = {
    autosize: true,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
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
      text: infoText,
      showarrow: false,
      font: { size: 11, color: '#e6edf3' },
      xanchor: 'center',
    }],
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {toolbar}
      <Plot
        data={data2d}
        layout={layout2d}
        useResizeHandler
        style={{ width: '100%', flex: 1 }}
        config={{ displayModeBar: false }}
      />
    </div>
  );
}
