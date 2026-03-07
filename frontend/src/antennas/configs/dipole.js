export default {
  id: 'dipole',
  label: 'Dipolo λ/2',
  description: 'Antenna a dipolo a mezza onda',
  defaultParams: { frequency_mhz: 300, length_mm: 475 },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza (MHz)', type: 'number', min: 1, step: 1 },
    { name: 'length_mm',     label: 'Lunghezza (mm)',  type: 'number', min: 1, step: 1 },
  ],
};
