export default {
  id: 'discone',
  label: 'Discone',
  description: 'Antenna discone a banda larga',
  defaultParams: { frequency_mhz: 400, cone_length_mm: 185, cone_angle_deg: 60, disc_diameter_mm: 150 },
  fields: [
    { name: 'frequency_mhz',    label: 'Frequenza (MHz)',     type: 'number', min: 1,  step: 1, max: 10000 },
    { name: 'cone_length_mm',   label: 'Lunghezza cono (mm)', type: 'number', min: 1,  step: 1, max: 925 },
    { name: 'cone_angle_deg',   label: 'Angolo cono (°)',     type: 'number', min: 10, step: 5, max: 90 },
    { name: 'disc_diameter_mm', label: 'Diametro disco (mm)', type: 'number', min: 1,  step: 1, max: 750 },
  ],
};
