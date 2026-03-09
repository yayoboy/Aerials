export default {
  id: 'lpda',
  label: 'LPDA',
  description: 'Log-Periodic Dipole Array — banda larga con guadagno direttivo moderato',
  defaultParams: { frequency_mhz: 150, tau: 0.90, sigma: 0.15, num_elements: 6 },
  derivedFromFreq(freqMhz) {
    return { frequency_mhz: Math.round(freqMhz) };
  },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza di progetto (MHz)', type: 'number', min: 1,    step: 1,    max: 10000 },
    { name: 'tau',           label: 'Fattore di scala τ (0.8–0.97)', type: 'number', min: 0.80, step: 0.01, max: 0.97  },
    { name: 'sigma',         label: 'Spaziatura relativa σ (0.05–0.25)', type: 'number', min: 0.05, step: 0.01, max: 0.25 },
    { name: 'num_elements',  label: 'Numero di elementi (3–12)',   type: 'number', min: 3,    step: 1,    max: 12    },
  ],
};
