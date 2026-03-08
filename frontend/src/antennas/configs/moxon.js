export default {
  id: 'moxon',
  label: 'Moxon Rectangle',
  description: 'Rettangolo Moxon compatto a 2 elementi (driven + reflector)',
  defaultParams: { frequency_mhz: 144, element_length_mm: 990, tail_length_mm: 171, feed_gap_mm: 27 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return {
      element_length_mm: Math.round(lam * 0.4762),
      tail_length_mm:    Math.round(lam * 0.0820),
      feed_gap_mm:       Math.round(lam * 0.0130 * 10) / 10,
    };
  },
  fields: [
    { name: 'frequency_mhz',     label: 'Frequenza (MHz)',          type: 'number', min: 1,   step: 1,   max: 10000 },
    { name: 'element_length_mm', label: 'Larghezza totale A (mm)',  type: 'number', min: 10,  step: 1,   max: 10000 },
    { name: 'tail_length_mm',    label: 'Lunghezza coda B (mm)',    type: 'number', min: 1,   step: 1,   max: 2000  },
    { name: 'feed_gap_mm',       label: 'Gap feed C (mm)',          type: 'number', min: 0.5, step: 0.5, max: 100   },
  ],
};
