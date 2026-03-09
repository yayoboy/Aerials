export default {
  id: 'turnstile',
  label: 'Turnstile',
  description: 'Due dipoli λ/2 incrociati a 90° — polarizzazione ellittica/circolare',
  defaultParams: { frequency_mhz: 144, arm_length_mm: 510 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { arm_length_mm: Math.round(lam / 4) };
  },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza (MHz)',           type: 'number', min: 1,  step: 1,   max: 10000 },
    { name: 'arm_length_mm', label: 'Lunghezza braccio (mm)',    type: 'number', min: 1,  step: 1,   max: 5000  },
  ],
};
