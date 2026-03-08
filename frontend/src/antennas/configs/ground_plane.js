export default {
  id: 'ground_plane',
  label: 'Ground Plane',
  description: 'Monopolo con radiali inclinati',
  defaultParams: { frequency_mhz: 146, radial_length_mm: 490, num_radials: 4, radial_angle_deg: 45 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return { radial_length_mm: Math.round(lam / 4) };
  },
  fields: [
    { name: 'frequency_mhz',    label: 'Frequenza (MHz)',       type: 'number', min: 1, step: 1, max: 10000 },
    { name: 'radial_length_mm', label: 'Lunghezza radiali (mm)', type: 'number', min: 1, step: 1, max: 2450 },
    { name: 'num_radials',      label: 'N. radiali',            type: 'number', min: 2, step: 1, max: 8 },
    { name: 'radial_angle_deg', label: 'Angolo radiali (°)',    type: 'number', min: 0, step: 5, max: 90 },
  ],
};
