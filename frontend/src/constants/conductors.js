export const MATERIALS = [
  { id: 'copper',   label: 'Rame (Cu)',        conductivity: 5.8e7, color: '#b87333' },
  { id: 'silver',   label: 'Argento (Ag)',      conductivity: 6.3e7, color: '#c0c0c0' },
  { id: 'aluminum', label: 'Alluminio (Al)',     conductivity: 3.5e7, color: '#848789' },
  { id: 'steel',    label: 'Acciaio inox',       conductivity: 1.4e6, color: '#8d8d8d' },
  { id: 'brass',    label: 'Ottone',             conductivity: 1.6e7, color: '#b5a642' },
  { id: 'custom',   label: 'Personalizzato',     conductivity: null,  color: '#ffffff' },
];

export const CROSS_SECTIONS = [
  { id: 'round',  label: 'Filo tondo',        fields: ['radius_mm'] },
  { id: 'tube',   label: 'Tubo',              fields: ['outer_diameter_mm', 'wall_thickness_mm'] },
  { id: 'flat',   label: 'Nastro piatto',     fields: ['width_mm', 'thickness_mm'] },
  { id: 'square', label: 'Profilo quadrato',  fields: ['width_mm'] },
];
