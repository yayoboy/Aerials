# UI Features v3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add frequency→length auto-derivation, SVG construction diagrams, contextual tooltip glossary, and Moxon antenna to the aerials app.

**Architecture:** Four independent feature areas: (1) glossary tooltip component applied to existing views, (2) `derivedFromFreq()` added to each antenna config consumed by `AntennaForm`, (3) `AntennaDiagram` component with per-antenna SVG drawing functions, (4) full Moxon antenna (backend FDTD + frontend config/geometry/diagram).

**Tech Stack:** React 19, Vite 7, SVG inline JSX, FastAPI + openEMS (backend), Pydantic v2

---

### Task 1: Glossary constants + component

**Files:**
- Create: `frontend/src/constants/glossary.js`
- Create: `frontend/src/components/Glossary.jsx`
- Modify: `frontend/src/App.css` (add tooltip CSS)

**Step 1: Create `frontend/src/constants/glossary.js`**

```js
export const GLOSSARY = {
  S11:          'Coefficiente di riflessione — misura quanta potenza viene riflessa all\'ingresso. Ideale < −10 dB.',
  VSWR:         'Voltage Standing Wave Ratio — rapporto d\'onda stazionaria. Ideale = 1:1 (< 2:1 accettabile).',
  SWR:          'Standing Wave Ratio — sinonimo di VSWR.',
  dB:           'Decibel — scala logaritmica. Ogni −10 dB = 10× meno potenza riflessa.',
  FDTD:         'Finite-Difference Time-Domain — metodo numerico per simulare la propagazione elettromagnetica.',
  λ:            'Lunghezza d\'onda = c / f  (c = 299 792 km/s). Determina le dimensioni fisiche dell\'antenna.',
  MHz:          'Megahertz — milioni di cicli al secondo.',
  GHz:          'Gigahertz — miliardi di cicli al secondo.',
  feed:         'Feed point — punto di alimentazione dove il cavo coassiale si connette all\'antenna.',
  'Return Loss': 'Perdita di ritorno = −S11 in dB. Più alto = meglio.',
  resonance:    'Frequenza di risonanza — dove S11 è minimo e l\'antenna trasferisce il massimo di potenza.',
  εr:           'Permittività relativa del substrato dielettrico (patch antenna). FR4 ≈ 4.4.',
};
```

**Step 2: Create `frontend/src/components/Glossary.jsx`**

```jsx
import { GLOSSARY } from '../constants/glossary.js';

export default function Glossary({ term, children }) {
  const def = GLOSSARY[term];
  if (!def) return <>{children}</>;
  return (
    <span className="glossary-term" data-tip={def}>
      {children}
    </span>
  );
}
```

**Step 3: Add CSS to `frontend/src/App.css`**

Add at the end of the file:
```css
.glossary-term {
  border-bottom: 1px dashed #8b949e;
  cursor: help;
  position: relative;
  white-space: nowrap;
}
.glossary-term::after {
  content: attr(data-tip);
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 7px 11px;
  font-size: 12px;
  line-height: 1.5;
  color: #c9d1d9;
  width: 240px;
  white-space: normal;
  z-index: 200;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.glossary-term:hover::after {
  display: block;
}
```

**Step 4: Verify by checking files exist and have correct content**

```bash
cat frontend/src/constants/glossary.js | head -5
cat frontend/src/components/Glossary.jsx
```

**Step 5: Commit**

```bash
git add frontend/src/constants/glossary.js frontend/src/components/Glossary.jsx frontend/src/App.css
git commit -m "feat: add Glossary component with contextual tooltip definitions"
```

---

### Task 2: Apply Glossary tooltips to S11Chart and AntennaSpecs

**Files:**
- Modify: `frontend/src/components/S11Chart.jsx`
- Modify: `frontend/src/components/AntennaSpecs.jsx`

**Step 1: Update `S11Chart.jsx`**

Add import at top:
```js
import Glossary from './Glossary.jsx';
```

Replace the S11/VSWR toggle buttons text:
```jsx
// Before:
>S11</button>
// ...
>VSWR</button>

// After:
><Glossary term="S11">S11</Glossary></button>
// ...
><Glossary term="VSWR">VSWR</Glossary></button>
```

Replace yAxis title (inside layout object, line ~171):
```js
// Before:
title: showVswr ? 'VSWR' : 'S11 (dB)',
// After:
title: showVswr ? 'VSWR' : 'S11 (dB)',   // Plotly axis titles are plain strings — leave as-is
```

Update the resonance annotation text to include unit label (no change needed — already shows MHz/dB).

**Step 2: Update `AntennaSpecs.jsx`**

Add import at top:
```js
import Glossary from './Glossary.jsx';
```

Wrap λ label in AntennaSpecs (line ~55):
```jsx
// Before:
<span className="spec-label">Lunghezza d'onda</span>
<span className="spec-value">λ = {lambdaMm} mm</span>

// After:
<span className="spec-label">Lunghezza d'onda</span>
<span className="spec-value"><Glossary term="λ">λ</Glossary> = {lambdaMm} mm</span>
```

Wrap feed-related label if present. Also wrap "Frequenza" label:
```jsx
// In the spec-row for frequency (around line 47):
<span className="spec-label">Frequenza</span>
// leave as-is (no acronym to explain)
```

**Step 3: Verify in browser**

Run `docker compose up` and hover over "S11", "VSWR", "λ" in the UI. Tooltip should appear.

**Step 4: Commit**

```bash
git add frontend/src/components/S11Chart.jsx frontend/src/components/AntennaSpecs.jsx
git commit -m "feat: apply Glossary tooltips to S11Chart and AntennaSpecs"
```

---

### Task 3: Add `derivedFromFreq` to all 12 existing antenna configs

**Files:**
- Modify: `frontend/src/antennas/configs/dipole.js`
- Modify: `frontend/src/antennas/configs/monopole.js`
- Modify: `frontend/src/antennas/configs/folded_dipole.js`
- Modify: `frontend/src/antennas/configs/inverted_v.js`
- Modify: `frontend/src/antennas/configs/sleeve.js`
- Modify: `frontend/src/antennas/configs/ground_plane.js`
- Modify: `frontend/src/antennas/configs/loop.js`
- Modify: `frontend/src/antennas/configs/yagi.js`
- Modify: `frontend/src/antennas/configs/discone.js`
- Modify: `frontend/src/antennas/configs/jpole.js`
- Modify: `frontend/src/antennas/configs/helix.js`
- Modify: `frontend/src/antennas/configs/patch.js`

**Formula helper (inline in each file):** `const lam = 299792.458 / freqMhz;`

**Step 1: Add `derivedFromFreq` to each config file**

**`dipole.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { length_mm: Math.round(lam / 2) };
},
```

**`monopole.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { length_mm: Math.round(lam / 4) };
},
```

**`folded_dipole.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { length_mm: Math.round(lam / 2) };
},
```

**`inverted_v.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { length_mm: Math.round(lam / 2) };
},
```

**`sleeve.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return {
    monopole_length_mm: Math.round(lam / 4),
    sleeve_length_mm:   Math.round(lam / 8),
  };
},
```

**`ground_plane.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { radial_length_mm: Math.round(lam / 4) };
},
```

**`loop.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { perimeter_mm: Math.round(lam) };
},
```

**`yagi.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return {
    driven_length_mm:    Math.round(lam / 2),
    reflector_length_mm: Math.round(lam / 2 * 1.05),
  };
},
```

**`discone.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { cone_length_mm: Math.round(lam / 4) };
},
```

**`jpole.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return {
    long_element_mm: Math.round(lam * 0.75),
    stub_length_mm:  Math.round(lam / 4),
  };
},
```

**`helix.js`** — add after `defaultParams`:
```js
derivedFromFreq(freqMhz) {
  const lam = 299792.458 / freqMhz;
  return { diameter_mm: Math.round(lam / Math.PI) };
},
```

**`patch.js`** — add after `defaultParams` (Pozar formula):
```js
derivedFromFreq(freqMhz, currentParams) {
  const er = (currentParams?.substrate_er) ?? 4.4;
  const h  = (currentParams?.substrate_height_mm) ?? 1.6;
  const c  = 299792458.0;
  const f  = freqMhz * 1e6;
  // Width (Pozar)
  const W = (c / (2 * f)) * Math.sqrt(2 / (er + 1)) * 1000;
  // Effective permittivity
  const er_eff = (er + 1) / 2 + (er - 1) / 2 * Math.pow(1 + 12 * h / W, -0.5);
  // Length extension
  const dL = 0.412 * h * (er_eff + 0.3) * (W / h + 0.264) / ((er_eff - 0.258) * (W / h + 0.8));
  // Resonant length
  const L = (c / (2 * f * Math.sqrt(er_eff))) * 1000 - 2 * dL;
  return {
    width_mm:  Math.round(W * 10) / 10,
    length_mm: Math.round(L * 10) / 10,
  };
},
```

> Note: `patch.js` `derivedFromFreq` takes an optional second argument `currentParams` to read `substrate_er` and `substrate_height_mm`. This requires a small change in Task 4 to pass `currentParams` for the patch antenna.

**Step 2: Verify configs export the function**

```bash
node -e "import('./frontend/src/antennas/configs/dipole.js').then(m => console.log(m.default.derivedFromFreq(144)))"
```
Expected: `{ length_mm: 1040 }`

**Step 3: Commit**

```bash
git add frontend/src/antennas/configs/
git commit -m "feat: add derivedFromFreq to all 12 antenna configs"
```

---

### Task 4: Update AntennaForm to auto-derive lengths on frequency change

**Files:**
- Modify: `frontend/src/components/AntennaForm.jsx:8`

**Step 1: Replace the `set` function in `AntennaForm.jsx`**

Current (line 8):
```js
const set = (name, value) => onChange({ ...params, [name]: value });
```

Replace with:
```js
const set = (name, value) => {
  const updated = { ...params, [name]: value };
  if (name === 'frequency_mhz' && typeof cfg.derivedFromFreq === 'function') {
    const derived = cfg.derivedFromFreq(value, params);
    onChange({ ...updated, ...derived });
  } else {
    onChange(updated);
  }
};
```

**Step 2: Verify in browser**

1. Start the app: `docker compose up`
2. Select "Dipolo λ/2"
3. Move the frequency slider from 300 MHz to 144 MHz
4. Verify: `length_mm` field updates automatically to ≈1040 mm (λ/2 at 144 MHz)
5. Manually type a different length → value stays
6. Move frequency again → length updates again

**Step 3: Commit**

```bash
git add frontend/src/components/AntennaForm.jsx
git commit -m "feat: auto-derive antenna lengths from frequency in AntennaForm"
```

---

### Task 5: Moxon antenna — frontend config + geometry + index

**Files:**
- Create: `frontend/src/antennas/configs/moxon.js`
- Create: `frontend/src/antennas/geometries/moxon.js`
- Modify: `frontend/src/antennas/configs/index.js`

**Step 1: Create `frontend/src/antennas/configs/moxon.js`**

```js
export default {
  id: 'moxon',
  label: 'Moxon Rectangle',
  description: 'Rettangolo Moxon compatto a 2 elementi (driven + reflector)',
  defaultParams: { frequency_mhz: 144, element_length_mm: 990, tail_length_mm: 171, feed_gap_mm: 27 },
  derivedFromFreq(freqMhz) {
    const lam = 299792.458 / freqMhz;
    return {
      element_length_mm: Math.round(lam * 0.4762),
      tail_length_mm:    Math.round(lam * 0.0820),
      feed_gap_mm:       Math.round(lam * 0.0130 * 10) / 10,
    };
  },
  fields: [
    { name: 'frequency_mhz',     label: 'Frequenza (MHz)',          type: 'number', min: 1,   step: 1,   max: 10000 },
    { name: 'element_length_mm', label: 'Larghezza totale A (mm)',  type: 'number', min: 10,  step: 1,   max: 10000 },
    { name: 'tail_length_mm',    label: 'Lunghezza coda B (mm)',    type: 'number', min: 1,   step: 1,   max: 2000  },
    { name: 'feed_gap_mm',       label: 'Gap feed C (mm)',          type: 'number', min: 0.5, step: 0.5, max: 100   },
  ],
};
```

**Step 2: Create `frontend/src/antennas/geometries/moxon.js`**

```js
import * as THREE from 'three';

export function buildMoxon(params, conductor, color) {
  const group  = new THREE.Group();
  const A      = (params.element_length_mm ?? 990) * 0.001;
  const B      = (params.tail_length_mm    ?? 171) * 0.001;
  const C      = (params.feed_gap_mm       ??  27) * 0.001;
  const radius = Math.max((conductor?.radius_mm ?? 1) * 0.001, A * 0.008);
  const lam    = 299792.458 / ((params.frequency_mhz ?? 144) * 1000);
  const D      = Math.max(lam * 0.001 * 0.071 - C - B * 2, 0.001);
  const depth  = B + D + B;

  const mat  = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const feed = new THREE.MeshStandardMaterial({ color: 0xff3333 });

  function addWire(x1, y1, z1, x2, y2, z2, mat) {
    const dx = x2-x1, dy = y2-y1, dz = z2-z1;
    const len = Math.sqrt(dx*dx + dy*dy + dz*dz);
    if (len < 1e-6) return;
    const geo = new THREE.CylinderGeometry(radius, radius, len, 8);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set((x1+x2)/2, (y1+y2)/2, (z1+z2)/2);
    mesh.lookAt(new THREE.Vector3(x2, y2, z2));
    mesh.rotateX(Math.PI / 2);
    group.add(mesh);
  }

  // Driven element (left and right halves)
  addWire(-A/2, 0, 0, -C/2, 0, 0, mat);
  addWire( C/2, 0, 0,  A/2, 0, 0, mat);
  // Left tail
  addWire(-A/2, 0, 0, -A/2, -B, 0, mat);
  // Right tail
  addWire( A/2, 0, 0,  A/2, -B, 0, mat);
  // Reflector
  addWire(-A/2, -depth, 0, A/2, -depth, 0, mat);
  // Reflector left tail
  addWire(-A/2, -depth+B, 0, -A/2, -depth, 0, mat);
  // Reflector right tail
  addWire( A/2, -depth+B, 0,  A/2, -depth, 0, mat);

  // Feed point
  const feedGeo = new THREE.SphereGeometry(radius * 3, 8, 8);
  group.add(new THREE.Mesh(feedGeo, feed));

  return group;
}
```

**Step 3: Update `frontend/src/antennas/configs/index.js`**

```js
import dipole       from './dipole.js';
import foldedDipole from './folded_dipole.js';
import monopole     from './monopole.js';
import yagi         from './yagi.js';
import invertedV    from './inverted_v.js';
import loop         from './loop.js';
import helix        from './helix.js';
import sleeve       from './sleeve.js';
import discone      from './discone.js';
import patch        from './patch.js';
import groundPlane  from './ground_plane.js';
import jpole        from './jpole.js';
import moxon        from './moxon.js';

export const ANTENNA_CONFIGS = [
  dipole, foldedDipole, monopole, yagi, invertedV, loop,
  helix, sleeve, discone, patch, groundPlane, jpole, moxon,
];

export const ANTENNA_MAP = Object.fromEntries(
  ANTENNA_CONFIGS.map(c => [c.id, c])
);
```

**Step 4: Wire Moxon geometry in Antenna3DView**

Read `frontend/src/components/Antenna3DView.jsx` first, then add moxon import and case similar to the other antennas.

**Step 5: Commit**

```bash
git add frontend/src/antennas/configs/moxon.js frontend/src/antennas/geometries/moxon.js frontend/src/antennas/configs/index.js frontend/src/components/Antenna3DView.jsx
git commit -m "feat: add Moxon Rectangle frontend config and 3D geometry"
```

---

### Task 6: Moxon antenna — backend

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/app/simulators/moxon.py`
- Modify: `backend/main.py`

**Step 1: Add `MoxonParams` to `backend/app/models.py`**

Add after `JPoleParams` (before `PatchParams`):
```python
class MoxonParams(BaseModel):
    frequency_mhz:     float = 144.0
    element_length_mm: float = 990.0
    tail_length_mm:    float = 171.0
    feed_gap_mm:       float = 27.0
```

**Step 2: Create `backend/app/simulators/moxon.py`**

```python
# backend/app/simulators/moxon.py
import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import MoxonParams

def simulate_moxon(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = MoxonParams(**params)

    try:
        import CSXCAD, openEMS
    except ImportError as e:
        raise

    f0     = p.frequency_mhz * 1e6
    A      = p.element_length_mm   # total width
    B      = p.tail_length_mm      # tail depth
    C      = p.feed_gap_mm         # feed gap
    radius = conductor.effective_radius_mm()

    c0         = 299792458.0
    lambda0    = c0 / f0 * 1000.0
    f_max      = f0 * 1.5
    lambda_min = c0 / f_max * 1000.0
    res        = lambda_min / 15.0

    # Gap between tail tips (Cebik formula: total depth ≈ 0.071λ)
    D = max(lambda0 * 0.071 - C - 2 * B, 1.0)
    depth = B + D + B

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    pad = lambda0 / 4.0

    mesh.AddLine('x', [-A/2 - pad, -A/2, -C/2, C/2, A/2, A/2 + pad])
    mesh.AddLine('y', [-pad, 0, B, B + D, depth, depth + pad])
    mesh.AddLine('z', [-pad - radius, 0, pad + radius])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('moxon')
    # Driven element halves
    metal.AddCylinder([-A/2, 0, 0], [-C/2, 0, 0], radius)
    metal.AddCylinder([ C/2, 0, 0], [ A/2, 0, 0], radius)
    # Driven element tails
    metal.AddCylinder([-A/2, 0, 0], [-A/2, B, 0], radius)
    metal.AddCylinder([ A/2, 0, 0], [ A/2, B, 0], radius)
    # Reflector
    metal.AddCylinder([-A/2, depth, 0], [A/2, depth, 0], radius)
    # Reflector tails
    metal.AddCylinder([-A/2, depth - B, 0], [-A/2, depth, 0], radius)
    metal.AddCylinder([ A/2, depth - B, 0], [ A/2, depth, 0], radius)

    # Feed port between driven element halves
    port = FDTD.AddLumpedPort(1, 50, [-C/2, 0, 0], [C/2, 0, 0], 'x', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_moxon_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'moxon.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {
            "antenna_type": "moxon",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
```

**Step 3: Add Moxon to `backend/main.py` in `_load_simulators()`**

Add after the jpole block:
```python
    try:
        from app.simulators.moxon import simulate_moxon
        simulators["moxon"] = simulate_moxon
    except ImportError as e:
        print(f"[WARNING] Could not load moxon simulator: {e}", flush=True)
```

Also update the count on the print line:
```python
# Before:
print(f"[INFO] Loaded {len(simulators)}/12 simulators: ...
# After:
print(f"[INFO] Loaded {len(simulators)}/13 simulators: ...
```

**Step 4: Verify syntax (outside Docker)**

```bash
cd backend && python3 -c "import ast; ast.parse(open('app/simulators/moxon.py').read()); print('OK')"
cd backend && python3 -c "import ast; ast.parse(open('app/models.py').read()); print('OK')"
cd backend && python3 -c "import ast; ast.parse(open('main.py').read()); print('OK')"
```

**Step 5: Commit**

```bash
git add backend/app/models.py backend/app/simulators/moxon.py backend/main.py
git commit -m "feat: add Moxon Rectangle backend FDTD simulator"
```

---

### Task 7: SVG diagram utils + AntennaDiagram component + all 13 diagram files

**Files:**
- Create: `frontend/src/antennas/diagrams/utils.js`
- Create: `frontend/src/antennas/diagrams/dipole.js`
- Create: `frontend/src/antennas/diagrams/monopole.js`
- Create: `frontend/src/antennas/diagrams/folded_dipole.js`
- Create: `frontend/src/antennas/diagrams/yagi.js`
- Create: `frontend/src/antennas/diagrams/inverted_v.js`
- Create: `frontend/src/antennas/diagrams/loop.js`
- Create: `frontend/src/antennas/diagrams/helix.js`
- Create: `frontend/src/antennas/diagrams/sleeve.js`
- Create: `frontend/src/antennas/diagrams/discone.js`
- Create: `frontend/src/antennas/diagrams/patch.js`
- Create: `frontend/src/antennas/diagrams/ground_plane.js`
- Create: `frontend/src/antennas/diagrams/jpole.js`
- Create: `frontend/src/antennas/diagrams/moxon.js`
- Create: `frontend/src/components/AntennaDiagram.jsx`

**Step 1: Create `frontend/src/antennas/diagrams/utils.js`**

```js
// Shared SVG drawing helpers for antenna construction diagrams
// All diagrams use viewBox="0 0 520 220"

export const VW = 520;
export const VH = 220;

// Horizontal dimension line with arrows and label
export function HDim({ x1, x2, y, label, above = true }) {
  const mx = (x1 + x2) / 2;
  const ly = above ? y - 8 : y + 16;
  const id = `arr-${Math.random().toString(36).slice(2)}`;
  return (
    <>
      <defs>
        <marker id={`${id}e`} viewBox="0 0 8 8" refX="8" refY="4" markerWidth="5" markerHeight="5" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
        <marker id={`${id}s`} viewBox="0 0 8 8" refX="0" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
      </defs>
      <line x1={x1} y1={y} x2={x2} y2={y} stroke="#6e7681" strokeWidth="0.8"
        markerStart={`url(#${id}s)`} markerEnd={`url(#${id}e)`} />
      <line x1={x1} y1={y-4} x2={x1} y2={y+4} stroke="#6e7681" strokeWidth="0.8" />
      <line x1={x2} y1={y-4} x2={x2} y2={y+4} stroke="#6e7681" strokeWidth="0.8" />
      <text x={mx} y={ly} textAnchor="middle" fill="#8b949e" fontSize="11">{label}</text>
    </>
  );
}

// Vertical dimension line
export function VDim({ x, y1, y2, label, left = true }) {
  const my = (y1 + y2) / 2;
  const lx = left ? x - 8 : x + 8;
  const anchor = left ? 'end' : 'start';
  const id = `arr-${Math.random().toString(36).slice(2)}`;
  return (
    <>
      <defs>
        <marker id={`${id}e`} viewBox="0 0 8 8" refX="8" refY="4" markerWidth="5" markerHeight="5" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
        <marker id={`${id}s`} viewBox="0 0 8 8" refX="0" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 Z" fill="#6e7681" />
        </marker>
      </defs>
      <line x1={x} y1={y1} x2={x} y2={y2} stroke="#6e7681" strokeWidth="0.8"
        markerStart={`url(#${id}s)`} markerEnd={`url(#${id}e)`} />
      <line x1={x-4} y1={y1} x2={x+4} y2={y1} stroke="#6e7681" strokeWidth="0.8" />
      <line x1={x-4} y1={y2} x2={x+4} y2={y2} stroke="#6e7681" strokeWidth="0.8" />
      <text x={lx} y={my + 4} textAnchor={anchor} fill="#8b949e" fontSize="11">{label}</text>
    </>
  );
}

// Horizontal wire (conductor)
export function HWire({ x1, x2, y, thick = 3 }) {
  return <line x1={x1} y1={y} x2={x2} y2={y} stroke="#58a6ff" strokeWidth={thick} strokeLinecap="round" />;
}

// Vertical wire
export function VWire({ x, y1, y2, thick = 3 }) {
  return <line x1={x} y1={y1} x2={x} y2={y2} stroke="#58a6ff" strokeWidth={thick} strokeLinecap="round" />;
}

// Feed point marker
export function FeedDot({ x, y, label = 'feed' }) {
  return (
    <>
      <circle cx={x} cy={y} r="5" fill="#f85149" />
      <text x={x} y={y + 17} textAnchor="middle" fill="#f85149" fontSize="10">{label}</text>
    </>
  );
}

// SVG wrapper with dark background
export function DiagramSVG({ children }) {
  return (
    <svg viewBox={`0 0 ${VW} ${VH}`} style={{ width: '100%', height: '100%', maxHeight: '220px' }}>
      <rect width={VW} height={VH} fill="transparent" />
      {children}
    </svg>
  );
}
```

**Step 2: Create `frontend/src/antennas/diagrams/dipole.js`**

```js
import { DiagramSVG, HWire, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { length_mm = 475, frequency_mhz = 300 } = params;
  const lam = Math.round(299792.458 / frequency_mhz);
  const cx = 260, wireY = 120;
  const scale = 400 / length_mm;
  const half = length_mm / 2 * scale;
  const gap = 5;

  return (
    <DiagramSVG>
      <HWire x1={cx - half} x2={cx - gap} y={wireY} />
      <HWire x1={cx + gap} x2={cx + half} y={wireY} />
      <FeedDot x={cx} y={wireY} />
      <HDim x1={cx - half} x2={cx - gap} y={wireY - 28} label={`${(length_mm/2).toFixed(0)} mm`} />
      <HDim x1={cx + gap} x2={cx + half} y={wireY - 28} label={`${(length_mm/2).toFixed(0)} mm`} />
      <HDim x1={cx - half} x2={cx + half} y={wireY + 35} label={`λ/2 = ${length_mm} mm  (λ=${lam} mm)`} above={false} />
    </DiagramSVG>
  );
}
```

**Step 3: Create `frontend/src/antennas/diagrams/monopole.js`**

```js
import { DiagramSVG, VWire, HWire, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { length_mm = 237, groundplane_mm = 300, frequency_mhz = 300 } = params;
  const lam = Math.round(299792.458 / frequency_mhz);
  const cx = 260, baseY = 150;
  const scaleV = Math.min(100 / length_mm, 0.5);
  const scaleH = Math.min(180 / groundplane_mm, 0.5);
  const mLen = length_mm * scaleV;
  const gpHalf = groundplane_mm / 2 * scaleH;

  return (
    <DiagramSVG>
      {/* Ground plane */}
      <HWire x1={cx - gpHalf} x2={cx + gpHalf} y={baseY} />
      {/* Monopole element */}
      <VWire x={cx} y1={baseY - mLen} y2={baseY} />
      <FeedDot x={cx} y={baseY} />
      <VDim x={cx - 18} y1={baseY - mLen} y2={baseY} label={`λ/4 = ${length_mm} mm`} />
      <HDim x1={cx - gpHalf} x2={cx + gpHalf} y={baseY + 30} label={`⌀ ${groundplane_mm} mm`} above={false} />
    </DiagramSVG>
  );
}
```

**Step 4: Create `frontend/src/antennas/diagrams/folded_dipole.js`**

```js
import { DiagramSVG, HWire, VWire, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { length_mm = 1020, frequency_mhz = 144 } = params;
  const lam = Math.round(299792.458 / frequency_mhz);
  const cx = 260, cy = 110;
  const scale = 400 / length_mm;
  const half = length_mm / 2 * scale;
  const h = 30, gap = 6;

  return (
    <DiagramSVG>
      {/* Top conductor */}
      <HWire x1={cx - half} x2={cx + half} y={cy - h/2} />
      {/* Bottom conductor with feed gap */}
      <HWire x1={cx - half} x2={cx - gap} y={cy + h/2} />
      <HWire x1={cx + gap} x2={cx + half} y={cy + h/2} />
      {/* Side connections */}
      <VWire x={cx - half} y1={cy - h/2} y2={cy + h/2} />
      <VWire x={cx + half} y1={cy - h/2} y2={cy + h/2} />
      <FeedDot x={cx} y={cy + h/2} />
      <HDim x1={cx - half} x2={cx + half} y={cy - h/2 - 22} label={`λ/2 = ${length_mm} mm`} />
      <HDim x1={cx - gap} x2={cx + gap} y={cy + h/2 + 28} label={`gap feed`} above={false} />
    </DiagramSVG>
  );
}
```

**Step 5: Create `frontend/src/antennas/diagrams/yagi.js`**

```js
import { DiagramSVG, HWire, VWire, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const {
    driven_length_mm = 1020, reflector_length_mm = 1050,
    director_lengths_mm = [980, 960], element_spacing_mm = 300,
  } = params;
  const dirs = Array.isArray(director_lengths_mm) ? director_lengths_mm : [director_lengths_mm];
  const allLengths = [reflector_length_mm, driven_length_mm, ...dirs];
  const maxLen = Math.max(...allLengths);
  const scaleH = 420 / maxLen;
  const totalElements = 2 + dirs.length;
  const scaleV = Math.min(160 / ((totalElements) * element_spacing_mm * scaleH * 0.6), 1);
  const spY = Math.min(element_spacing_mm * scaleH * scaleV, 45);
  const cx = 260;
  const startY = 30;
  const gap = 5;

  const rows = [
    { len: reflector_length_mm, y: startY, label: `Riflettore ${reflector_length_mm} mm`, isFed: false },
    { len: driven_length_mm,    y: startY + spY, label: `Dipolo ${driven_length_mm} mm`, isFed: true },
    ...dirs.map((d, i) => ({
      len: d, y: startY + spY * (2 + i),
      label: `Dir.${i+1} ${d} mm`, isFed: false,
    })),
  ];

  return (
    <DiagramSVG>
      {rows.map((r, i) => {
        const half = r.len / 2 * scaleH;
        return (
          <g key={i}>
            {r.isFed ? (
              <>
                <HWire x1={cx - half} x2={cx - gap} y={r.y} />
                <HWire x1={cx + gap} x2={cx + half} y={r.y} />
                <FeedDot x={cx} y={r.y} />
              </>
            ) : (
              <HWire x1={cx - half} x2={cx + half} y={r.y} />
            )}
            <text x={cx + half + 8} y={r.y + 4} fill="#8b949e" fontSize="10">{r.label}</text>
          </g>
        );
      })}
      {/* Boom */}
      <VWire x={cx} y1={startY} y2={rows[rows.length-1].y} thick={1.5} />
      {rows.length >= 2 && (
        <VDim x={cx - 22} y1={rows[0].y} y2={rows[1].y} label={`${element_spacing_mm} mm`} />
      )}
    </DiagramSVG>
  );
}
```

**Step 6: Create `frontend/src/antennas/diagrams/inverted_v.js`**

```js
import { DiagramSVG, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { length_mm = 20200, apex_angle_deg = 120, height_mm = 15000, frequency_mhz = 7 } = params;
  const armLen = length_mm / 2;
  const angleRad = (apex_angle_deg / 2) * Math.PI / 180;
  const cx = 260, apexY = 50;
  const scale = 180 / armLen;
  const dx = Math.sin(angleRad) * armLen * scale;
  const dy = Math.cos(angleRad) * armLen * scale;

  return (
    <DiagramSVG>
      {/* Left arm */}
      <line x1={cx} y1={apexY} x2={cx - dx} y2={apexY + dy} stroke="#58a6ff" strokeWidth="3" strokeLinecap="round" />
      {/* Right arm */}
      <line x1={cx} y1={apexY} x2={cx + dx} y2={apexY + dy} stroke="#58a6ff" strokeWidth="3" strokeLinecap="round" />
      {/* Ground line */}
      <line x1={cx - dx - 20} y1={apexY + dy} x2={cx + dx + 20} y2={apexY + dy} stroke="#6e7681" strokeWidth="1" strokeDasharray="4,3" />
      <FeedDot x={cx} y={apexY} label="feed (apex)" />
      <text x={cx} y={apexY + dy + 16} textAnchor="middle" fill="#8b949e" fontSize="10">GND</text>
      <HDim x1={cx - dx} x2={cx + dx} y={apexY + dy + 35} label={`λ/2 = ${length_mm} mm`} above={false} />
      <text x={cx + 8} y={(apexY + apexY + dy) / 2} fill="#8b949e" fontSize="10">{apex_angle_deg}°</text>
    </DiagramSVG>
  );
}
```

**Step 7: Create `frontend/src/antennas/diagrams/loop.js`**

```js
import { DiagramSVG, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { perimeter_mm = 21400, shape = 'square', frequency_mhz = 14 } = params;
  const lam = Math.round(299792.458 / frequency_mhz);
  const cx = 260, cy = 105;
  const size = 140;

  if (shape === 'square') {
    const half = size / 2;
    const feedX = cx, feedY = cy + half;
    return (
      <DiagramSVG>
        <rect x={cx - half} y={cy - half} width={size} height={size} fill="none" stroke="#58a6ff" strokeWidth="3" />
        <FeedDot x={feedX} y={feedY} />
        <text x={cx} y={cy} textAnchor="middle" fill="#8b949e" fontSize="11">λ = {perimeter_mm} mm</text>
        <text x={cx} y={cy + 16} textAnchor="middle" fill="#8b949e" fontSize="10">lato = {Math.round(perimeter_mm/4)} mm</text>
      </DiagramSVG>
    );
  }
  return (
    <DiagramSVG>
      <circle cx={cx} cy={cy} r={size/2} fill="none" stroke="#58a6ff" strokeWidth="3" />
      <FeedDot x={cx} y={cy + size/2} />
      <text x={cx} y={cy} textAnchor="middle" fill="#8b949e" fontSize="11">λ = {perimeter_mm} mm</text>
      <text x={cx} y={cy + 16} textAnchor="middle" fill="#8b949e" fontSize="10">⌀ = {Math.round(perimeter_mm/Math.PI)} mm</text>
    </DiagramSVG>
  );
}
```

**Step 8: Create `frontend/src/antennas/diagrams/helix.js`**

```js
import { DiagramSVG, VDim, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { diameter_mm = 40, pitch_mm = 30, turns = 8, frequency_mhz = 2400 } = params;
  const cx = 260, baseY = 180;
  const scaleD = Math.min(120 / diameter_mm, 2);
  const scaleP = Math.min(120 / (pitch_mm * turns), 1.5);
  const r = diameter_mm / 2 * scaleD;
  const totalH = pitch_mm * turns * scaleP;
  const points = [];
  for (let i = 0; i <= turns * 12; i++) {
    const t = (i / 12) * 2 * Math.PI;
    const x = cx + r * Math.cos(t);
    const y = baseY - (i / (turns * 12)) * totalH;
    points.push(`${x},${y}`);
  }

  return (
    <DiagramSVG>
      <polyline points={points.join(' ')} fill="none" stroke="#58a6ff" strokeWidth="2.5" />
      <FeedDot x={cx + r} y={baseY} />
      <VDim x={cx - r - 22} y1={baseY - totalH} y2={baseY} label={`${(pitch_mm * turns).toFixed(0)} mm`} />
      <HDim x1={cx - r} x2={cx + r} y={baseY - totalH - 18} label={`⌀ ${diameter_mm} mm`} />
      <text x={cx} y={baseY - totalH / 2} textAnchor="middle" fill="#8b949e" fontSize="10">{turns} spire</text>
    </DiagramSVG>
  );
}
```

**Step 9: Create `frontend/src/antennas/diagrams/sleeve.js`**

```js
import { DiagramSVG, VWire, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { monopole_length_mm = 490, sleeve_length_mm = 245, frequency_mhz = 144 } = params;
  const cx = 260, baseY = 170;
  const totalH = monopole_length_mm + sleeve_length_mm;
  const scale = Math.min(140 / totalH, 0.5);
  const mH = monopole_length_mm * scale;
  const sH = sleeve_length_mm * scale;
  const sleeveW = 14;

  return (
    <DiagramSVG>
      {/* Sleeve (outer conductor) */}
      <rect x={cx - sleeveW/2} y={baseY - sH} width={sleeveW} height={sH}
        fill="none" stroke="#58a6ff" strokeWidth="2.5" />
      {/* Monopole (inner) */}
      <VWire x={cx} y1={baseY - mH} y2={baseY} />
      <FeedDot x={cx} y={baseY} />
      <VDim x={cx + sleeveW/2 + 18} y1={baseY - sH} y2={baseY} label={`λ/8 = ${sleeve_length_mm} mm`} left={false} />
      <VDim x={cx - sleeveW/2 - 18} y1={baseY - mH} y2={baseY} label={`λ/4 = ${monopole_length_mm} mm`} />
    </DiagramSVG>
  );
}
```

**Step 10: Create `frontend/src/antennas/diagrams/discone.js`**

```js
import { DiagramSVG, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { cone_length_mm = 185, cone_angle_deg = 60, disc_diameter_mm = 150, frequency_mhz = 400 } = params;
  const cx = 260, apexY = 80;
  const scaleC = Math.min(120 / cone_length_mm, 0.6);
  const discScale = Math.min(100 / disc_diameter_mm, 0.5);
  const coneH = cone_length_mm * scaleC;
  const halfAngle = (cone_angle_deg / 2) * Math.PI / 180;
  const coneBase = Math.tan(halfAngle) * coneH;
  const discR = disc_diameter_mm / 2 * discScale;

  return (
    <DiagramSVG>
      {/* Disc */}
      <ellipse cx={cx} cy={apexY - 10} rx={discR} ry={discR * 0.3} fill="none" stroke="#58a6ff" strokeWidth="2.5" />
      {/* Cone */}
      <line x1={cx} y1={apexY} x2={cx - coneBase} y2={apexY + coneH} stroke="#58a6ff" strokeWidth="2.5" />
      <line x1={cx} y1={apexY} x2={cx + coneBase} y2={apexY + coneH} stroke="#58a6ff" strokeWidth="2.5" />
      <FeedDot x={cx} y={apexY} />
      <HDim x1={cx - discR} x2={cx + discR} y={apexY - 10 - 22} label={`⌀ disc ${disc_diameter_mm} mm`} />
      <VDim x={cx + coneBase + 18} y1={apexY} y2={apexY + coneH} label={`λ/4 = ${cone_length_mm} mm`} left={false} />
      <text x={cx + 18} y={apexY + coneH * 0.4} fill="#8b949e" fontSize="10">{cone_angle_deg}°</text>
    </DiagramSVG>
  );
}
```

**Step 11: Create `frontend/src/antennas/diagrams/patch.js`**

```js
import { DiagramSVG, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { width_mm = 38, length_mm = 29, substrate_height_mm = 1.6, substrate_er = 4.4 } = params;
  const cx = 260, cy = 100;
  const scale = Math.min(200 / Math.max(width_mm, length_mm), 3);
  const W = width_mm * scale;
  const L = length_mm * scale;
  const subH = Math.max(substrate_height_mm * scale * 3, 8);

  return (
    <DiagramSVG>
      {/* Substrate */}
      <rect x={cx - W/2 - 10} y={cy + L/2} width={W + 20} height={subH}
        fill="#1c2e4a" stroke="#30363d" strokeWidth="1" />
      <text x={cx} y={cy + L/2 + subH/2 + 4} textAnchor="middle" fill="#8b949e" fontSize="10">
        εr = {substrate_er} (h = {substrate_height_mm} mm)
      </text>
      {/* Ground plane */}
      <rect x={cx - W/2 - 10} y={cy + L/2 + subH} width={W + 20} height={5}
        fill="#58a6ff" stroke="none" />
      {/* Patch */}
      <rect x={cx - W/2} y={cy - L/2} width={W} height={L}
        fill="rgba(88,166,255,0.15)" stroke="#58a6ff" strokeWidth="2.5" />
      <FeedDot x={cx} y={cy + L/2} label="feed (edge)" />
      <HDim x1={cx - W/2} x2={cx + W/2} y={cy - L/2 - 18} label={`W = ${width_mm} mm`} />
      <VDim x={cx + W/2 + 18} y1={cy - L/2} y2={cy + L/2} label={`L = ${length_mm} mm`} left={false} />
    </DiagramSVG>
  );
}
```

**Step 12: Create `frontend/src/antennas/diagrams/ground_plane.js`**

```js
import { DiagramSVG, VWire, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { radial_length_mm = 490, num_radials = 4, radial_angle_deg = 45, frequency_mhz = 146 } = params;
  const cx = 260, baseY = 130;
  const scale = Math.min(80 / radial_length_mm, 0.25);
  const rLen = radial_length_mm * scale;
  const vLen = rLen;
  const angleRad = radial_angle_deg * Math.PI / 180;

  const radials = [];
  for (let i = 0; i < num_radials; i++) {
    const theta = (i / num_radials) * 2 * Math.PI + Math.PI/4;
    radials.push({ x: cx + Math.cos(theta) * rLen, y: baseY + Math.sin(theta) * rLen * Math.sin(angleRad) });
  }

  return (
    <DiagramSVG>
      {/* Radials */}
      {radials.map((r, i) => (
        <line key={i} x1={cx} y1={baseY} x2={r.x} y2={r.y} stroke="#58a6ff" strokeWidth="2.5" strokeLinecap="round" />
      ))}
      {/* Vertical element */}
      <VWire x={cx} y1={baseY - vLen} y2={baseY} />
      <FeedDot x={cx} y={baseY} />
      <VDim x={cx - 22} y1={baseY - vLen} y2={baseY} label={`λ/4 = ${radial_length_mm} mm`} />
      <text x={cx + 14} y={baseY + 24} fill="#8b949e" fontSize="10">{num_radials} radiali, {radial_angle_deg}°</text>
    </DiagramSVG>
  );
}
```

**Step 13: Create `frontend/src/antennas/diagrams/jpole.js`**

```js
import { DiagramSVG, VWire, HWire, VDim, HDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { long_element_mm = 1000, stub_length_mm = 330, stub_spacing_mm = 25, frequency_mhz = 146 } = params;
  const scale = Math.min(150 / long_element_mm, 0.2);
  const lH = long_element_mm * scale;
  const sH = stub_length_mm * scale;
  const sp = Math.max(stub_spacing_mm * scale * 3, 20);
  const cx = 260, baseY = 180;

  return (
    <DiagramSVG>
      {/* Long element */}
      <VWire x={cx + sp/2} y1={baseY - lH} y2={baseY} />
      {/* Stub */}
      <VWire x={cx - sp/2} y1={baseY - sH} y2={baseY} />
      {/* Bottom connection */}
      <HWire x1={cx - sp/2} x2={cx + sp/2} y={baseY} />
      {/* Feed point */}
      <FeedDot x={cx} y={baseY - sH} label="feed (stub top)" />
      <VDim x={cx + sp/2 + 20} y1={baseY - lH} y2={baseY} label={`3λ/4 = ${long_element_mm} mm`} left={false} />
      <VDim x={cx - sp/2 - 20} y1={baseY - sH} y2={baseY} label={`λ/4 = ${stub_length_mm} mm`} />
      <HDim x1={cx - sp/2} x2={cx + sp/2} y={baseY + 25} label={`${stub_spacing_mm} mm`} above={false} />
    </DiagramSVG>
  );
}
```

**Step 14: Create `frontend/src/antennas/diagrams/moxon.js`**

```js
import { DiagramSVG, HWire, VWire, HDim, VDim, FeedDot } from './utils.js';

export function buildDiagram(params) {
  const { element_length_mm = 990, tail_length_mm = 171, feed_gap_mm = 27, frequency_mhz = 144 } = params;
  const lam = 299792.458 / frequency_mhz;
  const D = Math.max(lam * 0.071 - feed_gap_mm - tail_length_mm * 2, 1);
  const totalDepth = tail_length_mm * 2 + D + feed_gap_mm;

  const scaleH = Math.min(380 / element_length_mm, 0.45);
  const scaleV = Math.min(150 / totalDepth, 0.8);
  const A = element_length_mm * scaleH;
  const B = tail_length_mm * scaleV;
  const C = Math.max(feed_gap_mm * scaleH, 6);
  const Ds = D * scaleV;
  const depth = B + Ds + B;

  const cx = 260, topY = 35;
  const gap = C / 2;

  return (
    <DiagramSVG>
      {/* Driven element (two halves) */}
      <HWire x1={cx - A/2} x2={cx - gap} y={topY} />
      <HWire x1={cx + gap} x2={cx + A/2} y={topY} />
      {/* Driven tails */}
      <VWire x={cx - A/2} y1={topY} y2={topY + B} />
      <VWire x={cx + A/2} y1={topY} y2={topY + B} />
      {/* Reflector */}
      <HWire x1={cx - A/2} x2={cx + A/2} y={topY + depth} />
      {/* Reflector tails */}
      <VWire x={cx - A/2} y1={topY + depth - B} y2={topY + depth} />
      <VWire x={cx + A/2} y1={topY + depth - B} y2={topY + depth} />
      <FeedDot x={cx} y={topY} />
      <HDim x1={cx - A/2} x2={cx + A/2} y={topY - 18} label={`A = ${element_length_mm} mm`} />
      <VDim x={cx + A/2 + 22} y1={topY} y2={topY + B} label={`B = ${tail_length_mm} mm`} left={false} />
      <VDim x={cx - A/2 - 22} y1={topY + B} y2={topY + B + Ds} label={`D = ${Math.round(D)} mm`} />
      <HDim x1={cx - gap} x2={cx + gap} y={topY + 18} label={`C = ${feed_gap_mm} mm`} above={false} />
    </DiagramSVG>
  );
}
```

**Step 15: Create `frontend/src/components/AntennaDiagram.jsx`**

```jsx
import { buildDiagram as dipoleDiagram }      from '../antennas/diagrams/dipole.js';
import { buildDiagram as monopoleDiagram }    from '../antennas/diagrams/monopole.js';
import { buildDiagram as foldedDiagram }      from '../antennas/diagrams/folded_dipole.js';
import { buildDiagram as yagiDiagram }        from '../antennas/diagrams/yagi.js';
import { buildDiagram as invertedVDiagram }   from '../antennas/diagrams/inverted_v.js';
import { buildDiagram as loopDiagram }        from '../antennas/diagrams/loop.js';
import { buildDiagram as helixDiagram }       from '../antennas/diagrams/helix.js';
import { buildDiagram as sleeveDiagram }      from '../antennas/diagrams/sleeve.js';
import { buildDiagram as disconeDiagram }     from '../antennas/diagrams/discone.js';
import { buildDiagram as patchDiagram }       from '../antennas/diagrams/patch.js';
import { buildDiagram as groundPlaneDiagram } from '../antennas/diagrams/ground_plane.js';
import { buildDiagram as jpoleDiagram }       from '../antennas/diagrams/jpole.js';
import { buildDiagram as moxonDiagram }       from '../antennas/diagrams/moxon.js';

const DIAGRAM_MAP = {
  dipole:        dipoleDiagram,
  monopole:      monopoleDiagram,
  folded_dipole: foldedDiagram,
  yagi:          yagiDiagram,
  inverted_v:    invertedVDiagram,
  loop:          loopDiagram,
  helix:         helixDiagram,
  sleeve:        sleeveDiagram,
  discone:       disconeDiagram,
  patch:         patchDiagram,
  ground_plane:  groundPlaneDiagram,
  jpole:         jpoleDiagram,
  moxon:         moxonDiagram,
};

export default function AntennaDiagram({ antennaType, params }) {
  const fn = DIAGRAM_MAP[antennaType];
  if (!fn) return null;
  return (
    <div style={{ width: '100%', height: '220px' }}>
      {fn(params)}
    </div>
  );
}
```

**Step 16: Commit all diagram files**

```bash
git add frontend/src/antennas/diagrams/ frontend/src/components/AntennaDiagram.jsx
git commit -m "feat: add SVG construction diagrams for all 13 antenna types"
```

---

### Task 8: Wire AntennaDiagram into App.jsx

**Files:**
- Modify: `frontend/src/App.jsx`

**Step 1: Add import at the top of `frontend/src/App.jsx`**

```js
import AntennaDiagram from './components/AntennaDiagram.jsx';
```

**Step 2: Add AntennaDiagram panel in the JSX, after the S11Chart glass-panel**

```jsx
{/* After the S11 glass-panel closing div, add: */}
<div className="glass-panel">
  <h2 className="panel-header">
    Diagramma costruttivo — {cfg?.label ?? antennaType}
  </h2>
  <div className="plot-container" style={{ height: '220px' }}>
    <AntennaDiagram antennaType={antennaType} params={params} />
  </div>
</div>
```

**Step 3: Verify in browser**

1. `docker compose up`
2. Open `http://localhost:5173`
3. Check that a construction diagram appears for the dipole
4. Switch antenna types — diagram should update
5. Move frequency slider — diagram dimensions should update in real-time

**Step 4: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wire AntennaDiagram into main app layout"
```

---

## Verification checklist

- [ ] Hover over "S11" in the chart toolbar → tooltip appears
- [ ] Hover over "λ" in AntennaSpecs → tooltip appears
- [ ] Change frequency on dipole → `length_mm` updates to λ/2
- [ ] Change frequency on patch → `width_mm` and `length_mm` update (Pozar formula)
- [ ] Moxon antenna appears in the selector
- [ ] Moxon 3D geometry renders in Antenna3DView
- [ ] Moxon simulation runs and returns S11 data
- [ ] Construction diagram shows for all 13 antenna types
- [ ] Diagram updates when params change
- [ ] Feed point is visible (red dot) in all diagrams
