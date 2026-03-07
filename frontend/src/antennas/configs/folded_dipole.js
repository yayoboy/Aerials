export default {
  id: 'folded_dipole',
  label: 'Dipolo Ripiegato',
  description: 'Folded dipole con impedenza ~300Ω',
  defaultParams: { frequency_mhz: 144, length_mm: 1020, spacing_mm: 25 },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza (MHz)',    type: 'number', min: 1,   step: 1 },
    { name: 'length_mm',     label: 'Lunghezza (mm)',     type: 'number', min: 1,   step: 1 },
    { name: 'spacing_mm',    label: 'Spaziatura fili (mm)', type: 'number', min: 1, step: 1 },
  ],
};
