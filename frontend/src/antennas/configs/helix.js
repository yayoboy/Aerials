export default {
  id: 'helix',
  label: 'Elica',
  description: 'Antenna elicoidale (assiale o normale)',
  defaultParams: { frequency_mhz: 2400, diameter_mm: 40, pitch_mm: 30, turns: 8, mode: 'axial' },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { diameter_mm: Math.round(lam / Math.PI) };
  },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza (MHz)',   type: 'number', min: 1,   step: 1, max: 10000 },
    { name: 'diameter_mm',   label: 'Diametro spira (mm)', type: 'number', min: 1, step: 1, max: 1000 },
    { name: 'pitch_mm',      label: 'Passo (mm)',         type: 'number', min: 1,  step: 1, max: 1000 },
    { name: 'turns',         label: 'N. spire',           type: 'number', min: 1,  step: 1, max: 50 },
    { name: 'mode', label: 'Modalità', type: 'select',
      options: [{ value: 'axial', label: 'Assiale' }, { value: 'normal', label: 'Normale' }] },
  ],
};
