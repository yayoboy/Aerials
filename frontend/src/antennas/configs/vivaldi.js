export default {
  id: 'vivaldi',
  label: 'Vivaldi (TSA)',
  description: 'Tapered Slot Antenna — ultra-wideband, radiazione end-fire, planare',
  defaultParams: { frequency_mhz: 2400, length_mm: 80, aperture_width_mm: 60, slot_width_mm: 3 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return {
      length_mm:         Math.round(lam * 0.8),
      aperture_width_mm: Math.round(lam * 0.6),
    };
  },
  fields: [
    { name: 'frequency_mhz',     label: 'Frequenza (MHz)',          type: 'number', min: 100, step: 10,  max: 10000 },
    { name: 'length_mm',         label: 'Lunghezza (mm)',           type: 'number', min: 5,   step: 1,   max: 1000  },
    { name: 'aperture_width_mm', label: 'Apertura (mm)',            type: 'number', min: 5,   step: 1,   max: 500   },
    { name: 'slot_width_mm',     label: 'Larghezza slot feed (mm)', type: 'number', min: 0.5, step: 0.5, max: 20    },
  ],
};
