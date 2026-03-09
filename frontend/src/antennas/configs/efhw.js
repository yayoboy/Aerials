export default {
  id: 'efhw',
  label: 'EFHW',
  description: 'End-Fed Half-Wave — S11 riferito a 2450 Ω (richiede trasformatore 49:1)',
  defaultParams: { frequency_mhz: 14, length_mm: 10100, counterpoise_mm: 1070 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return {
      length_mm:       Math.round(lam / 2 * 0.94),
      counterpoise_mm: Math.round(lam / 20),
    };
  },
  fields: [
    { name: 'frequency_mhz',   label: 'Frequenza (MHz)',          type: 'number', min: 1,   step: 1,   max: 30    },
    { name: 'length_mm',       label: 'Lunghezza filo (mm)',      type: 'number', min: 100, step: 10,  max: 200000 },
    { name: 'counterpoise_mm', label: 'Contrappeso (mm)',         type: 'number', min: 10,  step: 10,  max: 10000 },
  ],
};
