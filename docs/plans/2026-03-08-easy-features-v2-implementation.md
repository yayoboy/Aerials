# Easy Features v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add PNG export, live parameter sliders, and simulation history to the Aerials frontend.

**Architecture:** All changes are frontend-only (React + Plotly). No backend or API changes needed. Three independent features implemented in sequence: PNG export (1 file), sliders (12 config files + 1 component), history (App.jsx + new component + CSS).

**Tech Stack:** React 19, Plotly.js (via react-plotly.js), localStorage API

---

### Task 1: PNG Export in S11Chart

**Files:**
- Modify: `frontend/src/components/S11Chart.jsx`

The current `<Plot>` component doesn't expose a ref. We need a ref to access the underlying DOM element for `Plotly.downloadImage()`. The `react-plotly.js` `<Plot>` component accepts an `onInitialized` callback that provides the Plotly figure element, or we can use a wrapper div ref + `Plotly.newPlot` — but the simpler approach is using the `divId` prop and accessing the DOM element directly.

**Step 1: Add import and ref**

At the top of `S11Chart.jsx`, add `useRef` to the React import:
```js
import { useState, useRef } from 'react';
```

Add a ref below the state declarations:
```js
const plotRef = useRef(null);
```

**Step 2: Wire ref to Plot and implement download**

Add `divId="s11-plot"` to `<Plot>` and implement `downloadPng`:
```js
const downloadPng = () => {
  const el = document.getElementById('s11-plot');
  if (!el) return;
  // Plotly is available on window when react-plotly.js loads
  window.Plotly.downloadImage(el, {
    format: 'png',
    filename: 's11_chart',
    width: 900,
    height: 500,
  });
};
```

**Step 3: Add `[↓ PNG]` button to toolbar**

In the toolbar `<div>`, after the `[↓ CSV]` button:
```jsx
<button
  onClick={downloadPng}
  disabled={!results?.results}
  style={{
    padding: '4px 10px', fontSize: '12px', cursor: 'pointer',
    border: '1px solid #30363d', borderRadius: '6px',
    background: 'transparent', color: '#8b949e',
  }}
>↓ PNG</button>
```

**Step 4: Add `divId` prop to `<Plot>`**

```jsx
<Plot
  divId="s11-plot"
  data={...}
  ...
/>
```

**Step 5: Test manually**
- Run `cd frontend && npm run dev`
- Simulate any antenna
- Click `[↓ PNG]` → browser downloads `s11_chart.png`
- Verify button is disabled before simulation

**Step 6: Commit**
```bash
git add frontend/src/components/S11Chart.jsx
git commit -m "feat: add PNG export button to S11Chart"
```

---

### Task 2: Add `max` to all antenna config fields

**Files:**
- Modify: `frontend/src/antennas/configs/dipole.js`
- Modify: `frontend/src/antennas/configs/folded_dipole.js`
- Modify: `frontend/src/antennas/configs/monopole.js`
- Modify: `frontend/src/antennas/configs/yagi.js`
- Modify: `frontend/src/antennas/configs/inverted_v.js`
- Modify: `frontend/src/antennas/configs/loop.js`
- Modify: `frontend/src/antennas/configs/helix.js`
- Modify: `frontend/src/antennas/configs/sleeve.js`
- Modify: `frontend/src/antennas/configs/discone.js`
- Modify: `frontend/src/antennas/configs/patch.js`
- Modify: `frontend/src/antennas/configs/ground_plane.js`
- Modify: `frontend/src/antennas/configs/jpole.js`

The slider `<input type="range">` requires a `max` value. Add it to every `number` field. Skip `text` and `select` fields (no slider for those).

**Step 1: Add `max` to dipole.js**
```js
fields: [
  { name: 'frequency_mhz', label: 'Frequenza (MHz)', type: 'number', min: 1,   max: 10000, step: 1 },
  { name: 'length_mm',     label: 'Lunghezza (mm)',  type: 'number', min: 1,   max: 10000, step: 1 },
],
```

**Step 2: Add `max` to folded_dipole.js**

Read the file first, then add `max` to all number fields. Use `max: 10000` for length/freq fields. Typical defaults:
- `frequency_mhz: 300` → `max: 10000`
- `length_mm: 475` → `max: 10000`
- `gap_mm: 50` → `max: 500`

**Step 3: Add `max` to monopole.js**
- `frequency_mhz` → `max: 10000`
- `length_mm` → `max: 10000`

**Step 4: Add `max` to yagi.js**
- `frequency_mhz` → `max: 10000`
- `driven_length_mm`, `reflector_length_mm` → `max: 10000`
- `element_spacing_mm` → `max: 5000`
- `director_lengths_mm` → type `text`, skip

**Step 5: Add `max` to inverted_v.js**
- `frequency_mhz` → `max: 10000`
- length/angle fields → `max: 10000` for lengths, `max: 90` for angles

**Step 6: Add `max` to loop.js**
- `frequency_mhz` → `max: 10000`
- `diameter_mm` → `max: 10000`

**Step 7: Add `max` to helix.js**
- `frequency_mhz` → `max: 10000`
- `diameter_mm`, `pitch_mm` → `max: 1000`
- `turns` → `max: 50`
- `mode` → type `select`, skip

**Step 8: Add `max` to sleeve.js**
Read file, add `max` proportional to each field's default × 5.

**Step 9: Add `max` to discone.js**
Read file, add `max` proportional to each field's default × 5.

**Step 10: Add `max` to patch.js**
- `frequency_mhz` → `max: 10000`
- `width_mm`, `length_mm` → `max: 500`
- `substrate_er` → `max: 20`
- `substrate_height_mm` → `max: 10`

**Step 11: Add `max` to ground_plane.js**
Read file, add `max` proportional to each field's default × 5.

**Step 12: Add `max` to jpole.js**
Read file, add `max` proportional to each field's default × 5.

**Step 13: Commit**
```bash
git add frontend/src/antennas/configs/
git commit -m "feat: add max values to all antenna config fields for slider support"
```

---

### Task 3: Live sliders in AntennaForm

**Files:**
- Modify: `frontend/src/components/AntennaForm.jsx`
- Modify: `frontend/src/App.css`

Replace `<input type="number">` with a slider + number pair for fields where `type === 'number'`. Skip `text` and `select` fields.

**Step 1: Update AntennaForm.jsx number field rendering**

Replace the existing `type !== 'select'` branch with:
```jsx
field.type === 'number' ? (
  <div className="slider-row">
    <input
      type="range"
      className="param-slider"
      min={field.min ?? 1}
      max={field.max ?? (params[field.name] ?? 100) * 3}
      step={field.step ?? 1}
      value={params[field.name] ?? field.min ?? 1}
      onChange={e => set(field.name, parseFloat(e.target.value))}
    />
    <input
      type="number"
      className="form-input slider-number"
      min={field.min}
      max={field.max}
      step={field.step}
      value={params[field.name] ?? ''}
      onChange={e => {
        const v = e.target.value === '' ? '' : parseFloat(e.target.value);
        set(field.name, v);
      }}
    />
  </div>
) : field.type === 'select' ? (
  <select ...existing select code...>
) : (
  <input ...existing text code...>
)
```

**Step 2: Add CSS for slider row**

In `App.css`:
```css
/* ── Slider row ──────────────────────────────────────────────────────────── */
.slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-slider {
  flex: 1;
  accent-color: #2f81f7;
  cursor: pointer;
  min-width: 0;
}

.slider-number {
  width: 72px;
  flex-shrink: 0;
  text-align: right;
}
```

**Step 3: Test manually**
- `npm run dev`
- Select dipole → verify sliders appear for Frequenza and Lunghezza
- Drag slider → number updates, 3D view changes in real time
- Type in number input → slider thumb moves
- Select Yagi → verify `director_lengths_mm` (text field) shows plain text input, not slider

**Step 4: Commit**
```bash
git add frontend/src/components/AntennaForm.jsx frontend/src/App.css
git commit -m "feat: live parameter sliders in AntennaForm"
```

---

### Task 4: Simulation history

**Files:**
- Modify: `frontend/src/App.jsx`
- Create: `frontend/src/components/SimHistory.jsx`
- Modify: `frontend/src/App.css`

**Step 1: Add history helpers to App.jsx**

After the existing imports, add a localStorage utility at module level:
```js
const HISTORY_KEY = 'aerials_history';
const MAX_HISTORY = 10;

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]'); }
  catch { return []; }
}

function saveHistory(entries) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
}
```

**Step 2: Add history state to App component**

```js
const [history, setHistory] = useState(loadHistory);
```

**Step 3: Save to history after successful simulation**

In `handleSimulate`, after `setResults(data)`:
```js
// Compute resonance for display
const s11 = data.results.s11_db;
const freqs = data.results.frequencies_mhz;
const minIdx = s11.indexOf(Math.min(...s11));
const entry = {
  id: Date.now(),
  antenna_type: antennaType,
  label: cfg.label,
  params: { ...params },
  conductor: { ...conductor },
  results: data,
  resonance_mhz: freqs[minIdx],
  min_s11_db: s11[minIdx],
};
const updated = [entry, ...history.filter(h => h.id !== entry.id)].slice(0, MAX_HISTORY);
setHistory(updated);
saveHistory(updated);
```

**Step 4: Add restore and delete handlers**

```js
const handleRestoreHistory = (entry) => {
  setAntennaType(entry.antenna_type);
  setParams(entry.params);
  setConductor(entry.conductor);
  setResults(entry.results);
  setError(null);
};

const handleDeleteHistory = (id) => {
  const updated = history.filter(h => h.id !== id);
  setHistory(updated);
  saveHistory(updated);
};
```

**Step 5: Add SimHistory to sidebar in App.jsx**

After the error `<p>` and before closing `</aside>`:
```jsx
<SimHistory
  history={history}
  onRestore={handleRestoreHistory}
  onDelete={handleDeleteHistory}
/>
```

Add import at top:
```js
import SimHistory from './components/SimHistory.jsx';
```

**Step 6: Create SimHistory.jsx**

```jsx
// frontend/src/components/SimHistory.jsx
export default function SimHistory({ history, onRestore, onDelete }) {
  if (history.length === 0) return null;

  return (
    <div className="sim-history">
      <h3 className="section-title">Storico</h3>
      <ul className="history-list">
        {history.map(entry => (
          <li key={entry.id} className="history-item">
            <button className="history-restore" onClick={() => onRestore(entry)}>
              <span className="history-label">{entry.label}</span>
              <span className="history-meta">
                {entry.resonance_mhz?.toFixed(1)} MHz &nbsp;
                {entry.min_s11_db?.toFixed(1)} dB
              </span>
            </button>
            <button className="history-delete" onClick={() => onDelete(entry.id)}
                    title="Rimuovi">×</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Step 7: Add CSS for history**

In `App.css`:
```css
/* ── Simulation history ──────────────────────────────────────────────────── */
.sim-history {
  margin-top: 12px;
  border-top: 1px solid var(--border-color, #30363d);
  padding-top: 8px;
}

.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.history-restore {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 6px;
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border-color, #30363d);
  border-radius: 4px;
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  font-size: 11px;
  padding: 4px 6px;
  text-align: left;
  transition: border-color 0.15s, color 0.15s;
}

.history-restore:hover {
  border-color: #58a6ff;
  color: #f0f6fc;
}

.history-label {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-meta {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  color: var(--text-secondary, #8b949e);
}

.history-delete {
  background: none;
  border: none;
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 2px 4px;
  border-radius: 3px;
}

.history-delete:hover {
  color: #f85149;
}
```

**Step 8: Test manually**
- Run a simulation → entry appears in storico
- Run another with different antenna → two entries
- Click an entry → params + results restored (chart reappears, 3D updates)
- Click `×` → entry removed
- Refresh page → history persists (localStorage)
- Run 11 simulations → only 10 kept (oldest dropped)

**Step 9: Commit**
```bash
git add frontend/src/App.jsx frontend/src/components/SimHistory.jsx frontend/src/App.css
git commit -m "feat: simulation history with localStorage persistence"
```

---

### Task 5: Final verification

**Step 1: Run dev server**
```bash
cd frontend && npm run dev
```

**Step 2: Test all three features together**
- Sliders: drag frequency slider → 3D view updates
- Simulate → history entry appears, S11 chart shows
- `[↓ CSV]` → downloads CSV
- `[↓ PNG]` → downloads PNG
- `[Bande]` → band markers shown
- Toggle `[VSWR]` → green curve + VSWR=2 line
- Click history entry → restores state
- Delete entry → removed from list

**Step 3: Commit if any fixes needed**
```bash
git add -p
git commit -m "fix: <describe fix>"
```
