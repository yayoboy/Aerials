export default {
  id: 'yagi',
  label: 'Yagi-Uda',
  description: 'Antenna direttiva Yagi-Uda',
  defaultParams: {
    frequency_mhz: 144, driven_length_mm: 1020, reflector_length_mm: 1050,
    director_lengths_mm: [980, 960], element_spacing_mm: 300,
  },
  fields: [
    { name: 'frequency_mhz',       label: 'Frequenza (MHz)',         type: 'number', min: 1,   step: 1, max: 10000 },
    { name: 'driven_length_mm',    label: 'Lunghezza dipolo (mm)',   type: 'number', min: 1,   step: 1, max: 10000 },
    { name: 'reflector_length_mm', label: 'Lunghezza riflettore (mm)', type: 'number', min: 1, step: 1, max: 10000 },
    { name: 'element_spacing_mm',  label: 'Spaziatura elementi (mm)', type: 'number', min: 1,  step: 1, max: 5000 },
    { name: 'director_lengths_mm', label: 'Lunghezze direttori (mm, virgola)', type: 'text' },
  ],
};
