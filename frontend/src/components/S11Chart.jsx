// frontend/src/components/S11Chart.jsx
import { useState, useRef } from 'react';
import Plot from 'react-plotly.js';

const BANDS = [
  { name: '160m', fMin: 1.8,   fMax: 2.0   },
  { name: '80m',  fMin: 3.5,   fMax: 3.8   },
  { name: '40m',  fMin: 7.0,   fMax: 7.2   },
  { name: '30m',  fMin: 10.1,  fMax: 10.15 },
  { name: '20m',  fMin: 14.0,  fMax: 14.35 },
  { name: '17m',  fMin: 18.068,fMax: 18.168},
  { name: '15m',  fMin: 21.0,  fMax: 21.45 },
  { name: '12m',  fMin: 24.89, fMax: 24.99 },
  { name: '10m',  fMin: 28.0,  fMax: 29.7  },
  { name: '6m',   fMin: 50.0,  fMax: 52.0  },
  { name: '2m',   fMin: 144.0, fMax: 146.0 },
  { name: '70cm', fMin: 430.0, fMax: 440.0 },
];

function computeVswr(s11Db) {
  return s11Db.map(v => {
    const rho = Math.pow(10, v / 20);
    const denom = 1 - rho;
    if (Math.abs(denom) < 1e-9) return 999;
    return Math.min((1 + rho) / denom, 999);
  });
}

function exportCsv(freqs, s11, vswr) {
  const rows = ['freq_mhz,s11_db,vswr'];
  for (let i = 0; i < freqs.length; i++) {
    rows.push(`${freqs[i]},${s11[i].toFixed(3)},${vswr[i].toFixed(3)}`);
  }
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 's11_data.csv';
  a.click();
  URL.revokeObjectURL(url);
}

export default function S11Chart({ results, loading }) {
  const [showVswr,  setShowVswr]  = useState(false);
  const [showBands, setShowBands] = useState(false);

  const downloadPng = () => {
    const el = document.getElementById('s11-plot');
    if (!el) return;
    window.Plotly.downloadImage(el, {
      format: 'png',
      filename: 's11_chart',
      width: 900,
      height: 500,
    });
  };

  if (loading) return <div className="spinner" />;

  if (!results?.results) {
    return (
      <p style={{ color: 'var(--text-secondary)' }}>
        Configura i parametri e avvia la simulazione.
      </p>
    );
  }

  const freqs = results.results.frequencies_mhz;
  const s11   = results.results.s11_db;
  const vswr  = computeVswr(s11);

  // Resonance: index of minimum S11
  const minIdx  = s11.indexOf(Math.min(...s11));
  const fRes    = freqs[minIdx];
  const s11Res  = s11[minIdx];
  const vswrRes = vswr[minIdx];

  const fMin = Math.min(...freqs);
  const fMax = Math.max(...freqs);

  // Band shapes (only those overlapping the plot range)
  const bandShapes = showBands
    ? BANDS.filter(b => b.fMax >= fMin && b.fMin <= fMax).map(b => ({
        type: 'rect',
        xref: 'x', yref: 'paper',
        x0: Math.max(b.fMin, fMin), x1: Math.min(b.fMax, fMax),
        y0: 0, y1: 1,
        fillcolor: 'rgba(255,193,7,0.08)',
        line: { width: 0 },
        layer: 'below',
      }))
    : [];

  const bandAnnotations = showBands
    ? BANDS.filter(b => b.fMax >= fMin && b.fMin <= fMax).map(b => ({
        xref: 'x', yref: 'paper',
        x: (Math.max(b.fMin, fMin) + Math.min(b.fMax, fMax)) / 2,
        y: 0.98,
        text: b.name,
        showarrow: false,
        font: { size: 9, color: 'rgba(255,193,7,0.5)' },
        textangle: -90,
        xanchor: 'center', yanchor: 'top',
      }))
    : [];

  // Resonance marker
  const resonanceShape = {
    type: 'line',
    xref: 'x', yref: 'paper',
    x0: fRes, x1: fRes,
    y0: 0, y1: 1,
    line: { color: '#f85149', width: 1.5, dash: 'dash' },
  };

  const resonanceAnnotation = {
    xref: 'x', yref: 'paper',
    x: fRes, y: 0.02,
    text: showVswr
      ? `${fRes.toFixed(1)} MHz<br>VSWR ${vswrRes.toFixed(2)}`
      : `${fRes.toFixed(1)} MHz<br>${s11Res.toFixed(1)} dB`,
    showarrow: false,
    font: { size: 10, color: '#f85149' },
    bgcolor: 'rgba(13,17,23,0.7)',
    borderpad: 3,
    xanchor: 'left',
    yanchor: 'bottom',
  };

  const shapes      = [resonanceShape, ...bandShapes];
  const annotations = [resonanceAnnotation, ...bandAnnotations];

  const mainTrace = showVswr
    ? {
        x: freqs, y: vswr,
        type: 'scatter', mode: 'lines+markers',
        marker: { color: '#3fb950', size: 6 },
        line:   { color: '#3fb950', width: 2 },
        name: 'VSWR',
      }
    : {
        x: freqs, y: s11,
        type: 'scatter', mode: 'lines+markers',
        marker: { color: '#2f81f7', size: 6 },
        line:   { color: '#2f81f7', width: 2 },
        name: 'S11',
      };

  const vswrThreshold = showVswr
    ? [{
        x: [fMin, fMax], y: [2, 2],
        type: 'scatter', mode: 'lines',
        line: { color: 'rgba(248,81,73,0.5)', width: 1, dash: 'dot' },
        name: 'VSWR = 2',
        hoverinfo: 'skip',
      }]
    : [];

  const layout = {
    autosize: true,
    paper_bgcolor: 'transparent',
    plot_bgcolor:  'transparent',
    font: { color: '#8b949e', family: 'Inter' },
    xaxis: {
      title: 'Frequenza (MHz)',
      gridcolor: 'rgba(240,246,252,0.1)',
      zerolinecolor: 'rgba(240,246,252,0.2)',
    },
    yaxis: {
      title: showVswr ? 'VSWR' : 'S11 (dB)',
      gridcolor: 'rgba(240,246,252,0.1)',
      zerolinecolor: 'rgba(240,246,252,0.2)',
    },
    margin: { t: 20, r: 20, l: 60, b: 60 },
    shapes,
    annotations,
    legend: { font: { color: '#8b949e' }, bgcolor: 'transparent' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
        <div style={{ display: 'flex', borderRadius: '6px', overflow: 'hidden', border: '1px solid #30363d' }}>
          <button
            onClick={() => setShowVswr(false)}
            style={{
              padding: '4px 10px', fontSize: '12px', cursor: 'pointer', border: 'none',
              background: !showVswr ? '#1c2e4a' : 'transparent',
              color: !showVswr ? '#f0f6fc' : '#8b949e',
            }}
          >S11</button>
          <button
            onClick={() => setShowVswr(true)}
            style={{
              padding: '4px 10px', fontSize: '12px', cursor: 'pointer', border: 'none',
              background: showVswr ? '#1c2e4a' : 'transparent',
              color: showVswr ? '#f0f6fc' : '#8b949e',
            }}
          >VSWR</button>
        </div>

        <button
          onClick={() => setShowBands(b => !b)}
          style={{
            padding: '4px 10px', fontSize: '12px', cursor: 'pointer',
            border: '1px solid #30363d', borderRadius: '6px',
            background: showBands ? '#1c2e4a' : 'transparent',
            color: showBands ? '#f0f6fc' : '#8b949e',
          }}
        >Bande</button>

        <button
          onClick={() => exportCsv(freqs, s11, vswr)}
          style={{
            padding: '4px 10px', fontSize: '12px', cursor: 'pointer',
            border: '1px solid #30363d', borderRadius: '6px',
            background: 'transparent', color: '#8b949e',
            marginLeft: 'auto',
          }}
        >↓ CSV</button>

        <button
          onClick={downloadPng}
          disabled={!results?.results}
          style={{
            padding: '4px 10px', fontSize: '12px', cursor: 'pointer',
            border: '1px solid #30363d', borderRadius: '6px',
            background: 'transparent', color: '#8b949e',
            marginLeft: '4px',
          }}
        >↓ PNG</button>
      </div>

      {/* Chart */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <Plot
          divId="s11-plot"
          data={[mainTrace, ...vswrThreshold]}
          layout={layout}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
}
