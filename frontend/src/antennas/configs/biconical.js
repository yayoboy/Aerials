export default {
  id: 'biconical',
  label: 'Biconica',
  description: 'Due coni contrapposti — banda larghissima, usata per misure EMC e UHF',
  defaultParams: { frequency_mhz: 300, cone_length_mm: 250, cone_angle_deg: 60 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { cone_length_mm: Math.round(lam / 4) };
  },
  fields: [
    { name: 'frequency_mhz',  label: 'Frequenza (MHz)',             type: 'number', min: 1,  step: 1,  max: 10000 },
    { name: 'cone_length_mm', label: 'Lunghezza cono (mm)',         type: 'number', min: 5,  step: 1,  max: 2000  },
    { name: 'cone_angle_deg', label: 'Semi-angolo cono (°)',        type: 'number', min: 10, step: 1,  max: 80    },
  ],
};
