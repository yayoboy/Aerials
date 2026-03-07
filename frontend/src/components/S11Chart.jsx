// frontend/src/components/S11Chart.jsx
import Plot from 'react-plotly.js';

export default function S11Chart({ results, loading }) {
  if (loading) {
    return <div className="spinner" />;
  }

  if (!results?.results) {
    return (
      <p style={{ color: 'var(--text-secondary)' }}>
        Configura i parametri e avvia la simulazione.
      </p>
    );
  }

  return (
    <Plot
      data={[{
        x: results.results.frequencies_mhz,
        y: results.results.s11_db,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color: '#2f81f7', size: 6 },
        line:   { color: '#2f81f7', width: 2 },
        name: 'S11',
      }]}
      layout={{
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
          title: 'S11 (dB)',
          gridcolor: 'rgba(240,246,252,0.1)',
          zerolinecolor: 'rgba(240,246,252,0.2)',
        },
        margin: { t: 20, r: 20, l: 60, b: 60 },
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
    />
  );
}
