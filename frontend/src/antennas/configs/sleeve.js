export default {
  id: 'sleeve',
  label: 'Sleeve/Bazooka',
  description: 'Antenna a manica con balun integrato',
  defaultParams: { frequency_mhz: 144, monopole_length_mm: 490, sleeve_length_mm: 245 },
  fields: [
    { name: 'frequency_mhz',      label: 'Frequenza (MHz)',       type: 'number', min: 1, step: 1 },
    { name: 'monopole_length_mm', label: 'Lunghezza monopolo (mm)', type: 'number', min: 1, step: 1 },
    { name: 'sleeve_length_mm',   label: 'Lunghezza manica (mm)', type: 'number', min: 1, step: 1 },
  ],
};
