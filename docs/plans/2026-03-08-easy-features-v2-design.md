# Design: Easy Features v2

**Date:** 2026-03-08
**Status:** Approved

## Scope

Three frontend-only features for the Aerials antenna simulator. No backend changes required.

## Features

### 1. Export PNG

Add `[↓ PNG]` button to the existing S11Chart toolbar (next to `[↓ CSV]`).

- Use a React ref on `<Plot>` to access the underlying Plotly DOM element
- Call `Plotly.downloadImage(el, { format: 'png', filename: 's11_chart', width: 900, height: 500 })`
- Plotly is already bundled via `react-plotly.js` — no new dependencies
- Button disabled when no results

**File:** `frontend/src/components/S11Chart.jsx`

### 2. Live Sliders

Replace plain `<input type="number">` fields in `AntennaForm` with a slider + numeric input pair.

- Each field shows: `[range slider ════●════] [number input] mm`
- `min`, `max`, `step` added to each field definition in `antennas/configs/index.js` (all 12 configs)
- Fallback: if no min/max defined, use `[defaultValue * 0.1, defaultValue * 3]`
- Both controls are kept in sync (slider updates number, number updates slider)
- 3D view updates in real time (already wired via `params` state in `App.jsx`)
- Simulate button unchanged — still required to run FDTD

**Files:**
- `frontend/src/antennas/configs/index.js` — add `min`, `max`, `step` to each field
- `frontend/src/components/AntennaForm.jsx` — render slider + number pair

### 3. Simulation History

After each successful simulation, save a record to `localStorage` key `aerials_history` (JSON array, max 10 entries, newest first).

Record shape:
```json
{
  "id": 1709900000000,
  "antenna_type": "dipole",
  "label": "Dipolo",
  "params": { "length_mm": 1000, "frequency_mhz": 145 },
  "conductor": { "material": "copper", "cross_section": "round", "radius_mm": 1.0 },
  "results": { "frequencies_mhz": [...], "s11_db": [...] },
  "resonance_mhz": 145.3,
  "min_s11_db": -18.4
}
```

A `SimHistory` component in the sidebar shows a compact list. Each row:
```
Dipolo  145.3 MHz  −18.4 dB   [×]
```

Clicking a row restores `antennaType`, `params`, `conductor`, and `results` — no API call.
`[×]` deletes that entry from history.

**Files:**
- `frontend/src/App.jsx` — save to history after simulation, pass history state to `SimHistory`
- `frontend/src/components/SimHistory.jsx` — new component
- `frontend/src/App.css` — history list styles

## Layout Summary

**Sidebar (bottom, below simulate button):**
```
[Avvia simulazione FDTD]
─────────────────────────
Dipolo       145.3 MHz  −18.4 dB  [×]
Yagi 3el     435.0 MHz  −22.1 dB  [×]
```

**S11Chart toolbar (extended):**
```
[ S11 | VSWR ]    [ Bande ]    [ ↓ CSV ]  [ ↓ PNG ]
```

**AntennaForm field:**
```
Lunghezza (mm)
[━━━━━━●━━━━━] 1000
```

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/components/S11Chart.jsx` | Add PNG button + Plot ref |
| `frontend/src/antennas/configs/index.js` | Add min/max/step to all fields |
| `frontend/src/components/AntennaForm.jsx` | Slider + number pair |
| `frontend/src/App.jsx` | History save logic + SimHistory integration |
| `frontend/src/components/SimHistory.jsx` | New component |
| `frontend/src/App.css` | Slider and history styles |
