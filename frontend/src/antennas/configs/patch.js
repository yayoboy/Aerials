export default {
  id: 'patch',
  label: 'Patch Microstrip',
  description: 'Antenna patch su substrato dielettrico',
  defaultParams: { frequency_mhz: 2400, width_mm: 38, length_mm: 29, substrate_er: 4.4, substrate_height_mm: 1.6 },
  derivedFromFreq(freqMhz, currentParams) {
    const er = (currentParams?.substrate_er) ?? 4.4;
    const h  = (currentParams?.substrate_height_mm) ?? 1.6;
    const c  = 299792458.0;
    const f  = freqMhz * 1e6;
    const W = (c / (2 * f)) * Math.sqrt(2 / (er + 1)) * 1000;
    const er_eff = (er + 1) / 2 + (er - 1) / 2 * Math.pow(1 + 12 * h / W, -0.5);
    const dL = 0.412 * h * (er_eff + 0.3) * (W / h + 0.264) / ((er_eff - 0.258) * (W / h + 0.8));
    const L = (c / (2 * f * Math.sqrt(er_eff))) * 1000 - 2 * dL;
    return {
      width_mm:  Math.round(W * 10) / 10,
      length_mm: Math.round(L * 10) / 10,
    };
  },
  fields: [
    { name: 'frequency_mhz',       label: 'Frequenza (MHz)',     type: 'number', min: 100,  step: 10, max: 10000 },
    { name: 'width_mm',            label: 'Larghezza patch (mm)', type: 'number', min: 1,   step: 0.1, max: 500 },
    { name: 'length_mm',           label: 'Lunghezza patch (mm)', type: 'number', min: 1,   step: 0.1, max: 500 },
    { name: 'substrate_er',        label: 'Permittività rel. (εr)', type: 'number', min: 1, step: 0.1, max: 20 },
    { name: 'substrate_height_mm', label: 'Spessore substrato (mm)', type: 'number', min: 0.1, step: 0.1, max: 10 },
  ],
};
