export default {
  id: 'inverted_v',
  label: 'Inverted-V',
  description: 'Dipolo a forma di V invertita',
  defaultParams: { frequency_mhz: 7, length_mm: 20200, apex_angle_deg: 120, height_mm: 15000 },
  fields: [
    { name: 'frequency_mhz',  label: 'Frequenza (MHz)',  type: 'number', min: 1,   step: 0.1 },
    { name: 'length_mm',      label: 'Lunghezza (mm)',   type: 'number', min: 1,   step: 100 },
    { name: 'apex_angle_deg', label: 'Angolo apice (°)', type: 'number', min: 60,  step: 5, max: 150 },
    { name: 'height_mm',      label: 'Altezza apice (mm)', type: 'number', min: 100, step: 100 },
  ],
};
