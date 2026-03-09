export default {
  id: 'collinear',
  label: 'Array Collineare',
  description: 'N dipoli λ/2 impilati in linea — guadagno omnidirezionale verso l\'orizzonte',
  defaultParams: { frequency_mhz: 146, element_length_mm: 1026, num_elements: 4 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { element_length_mm: Math.round(lam / 2) };
  },
  fields: [
    { name: 'frequency_mhz',     label: 'Frequenza (MHz)',           type: 'number', min: 1,  step: 1,  max: 10000 },
    { name: 'element_length_mm', label: 'Lunghezza elemento (mm)',   type: 'number', min: 1,  step: 1,  max: 5000  },
    { name: 'num_elements',      label: 'Numero di elementi (2–8)',  type: 'number', min: 2,  step: 1,  max: 8     },
  ],
};
