export default {
  id: 'loop',
  label: 'Loop',
  description: 'Antenna a loop chiuso',
  defaultParams: { frequency_mhz: 14, perimeter_mm: 21400, shape: 'square' },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza (MHz)',   type: 'number', min: 1,   step: 0.1 },
    { name: 'perimeter_mm',  label: 'Perimetro (mm)',    type: 'number', min: 100, step: 100 },
    { name: 'shape', label: 'Forma', type: 'select',
      options: [{ value: 'square', label: 'Quadrato' }, { value: 'circular', label: 'Circolare' }] },
  ],
};
