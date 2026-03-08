export default {
  id: 'dipole',
  label: 'Dipolo λ/2',
  description: 'Antenna a dipolo a mezza onda',
  defaultParams: { frequency_mhz: 300, length_mm: 475 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { length_mm: Math.round(lam / 2) };
  },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza (MHz)', type: 'number', min: 1, step: 1, max: 10000 },
    { name: 'length_mm',     label: 'Lunghezza (mm)',  type: 'number', min: 1, step: 1, max: 10000 },
  ],
};
