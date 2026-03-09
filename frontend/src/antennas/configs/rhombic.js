export default {
  id: 'rhombic',
  label: 'Rombica',
  description: 'Quadrilatero a rombo con resistenza di terminazione — HF ad alto guadagno',
  defaultParams: { frequency_mhz: 14, leg_length_mm: 20000, apex_angle_deg: 60 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { leg_length_mm: Math.round(lam * 2) };
  },
  fields: [
    { name: 'frequency_mhz',  label: 'Frequenza (MHz)',          type: 'number', min: 1,  step: 1,  max: 30    },
    { name: 'leg_length_mm',  label: 'Lunghezza lato (mm)',      type: 'number', min: 100, step: 100, max: 100000 },
    { name: 'apex_angle_deg', label: 'Angolo apicale (°)',       type: 'number', min: 20, step: 1,  max: 120   },
  ],
};
