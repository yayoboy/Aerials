export default {
  id: 'monopole',
  label: 'Monopolo',
  description: 'Monopolo λ/4 su piano di massa',
  defaultParams: { frequency_mhz: 300, length_mm: 237.5, groundplane_mm: 300 },
  fields: [
    { name: 'frequency_mhz',  label: 'Frequenza (MHz)',       type: 'number', min: 1, step: 1, max: 10000 },
    { name: 'length_mm',      label: 'Lunghezza (mm)',        type: 'number', min: 1, step: 1, max: 1200 },
    { name: 'groundplane_mm', label: 'Diametro piano (mm)',   type: 'number', min: 1, step: 1, max: 1500 },
  ],
};
