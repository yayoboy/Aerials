export default {
  id: 'jpole',
  label: 'J-Pole',
  description: 'Antenna J-Pole con stub λ/4',
  defaultParams: { frequency_mhz: 146, long_element_mm: 1000, stub_length_mm: 330, stub_spacing_mm: 25 },
  fields: [
    { name: 'frequency_mhz',   label: 'Frequenza (MHz)',       type: 'number', min: 1, step: 1 },
    { name: 'long_element_mm', label: 'Elemento lungo (mm)',   type: 'number', min: 1, step: 1 },
    { name: 'stub_length_mm',  label: 'Lunghezza stub (mm)',   type: 'number', min: 1, step: 1 },
    { name: 'stub_spacing_mm', label: 'Spaziatura stub (mm)',  type: 'number', min: 1, step: 1 },
  ],
};
