export default {
  id: 'patch',
  label: 'Patch Microstrip',
  description: 'Antenna patch su substrato dielettrico',
  defaultParams: { frequency_mhz: 2400, width_mm: 38, length_mm: 29, substrate_er: 4.4, substrate_height_mm: 1.6 },
  fields: [
    { name: 'frequency_mhz',       label: 'Frequenza (MHz)',     type: 'number', min: 100,  step: 10 },
    { name: 'width_mm',            label: 'Larghezza patch (mm)', type: 'number', min: 1,   step: 0.1 },
    { name: 'length_mm',           label: 'Lunghezza patch (mm)', type: 'number', min: 1,   step: 0.1 },
    { name: 'substrate_er',        label: 'Permittività rel. (εr)', type: 'number', min: 1, step: 0.1 },
    { name: 'substrate_height_mm', label: 'Spessore substrato (mm)', type: 'number', min: 0.1, step: 0.1 },
  ],
};
