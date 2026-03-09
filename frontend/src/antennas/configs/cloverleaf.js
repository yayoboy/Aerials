export default {
  id: 'cloverleaf',
  label: 'Cloverleaf',
  description: 'Tre loop circolari inclinati a 120° — polarizzazione circolare per FPV/droni',
  defaultParams: { frequency_mhz: 5800, loop_diameter_mm: 16.5, tilt_deg: 40 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { loop_diameter_mm: parseFloat((lam / Math.PI).toFixed(1)) };
  },
  fields: [
    { name: 'frequency_mhz',    label: 'Frequenza (MHz)',             type: 'number', min: 100,  step: 10,  max: 10000 },
    { name: 'loop_diameter_mm', label: 'Diametro loop (mm)',          type: 'number', min: 1,    step: 0.5, max: 500   },
    { name: 'tilt_deg',         label: 'Inclinazione petali (°)',     type: 'number', min: 10,   step: 1,   max: 70    },
  ],
};
