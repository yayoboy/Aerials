# 3D Radiation Pattern Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a 3D radiation pattern diagram (Plotly surface) computed via openEMS near-to-far-field transform, triggered by a separate `[Calcola diagramma]` button after S11 simulation.

**Architecture:** Each of the 12 backend simulator functions gains a `with_radiation=False` flag; when `True`, a NF2FF box is added to the FDTD simulation and the far-field is computed post-run. A new `/radiation/{antenna_type}` FastAPI endpoint invokes simulators with this flag. On the frontend, `RadiationView.jsx` converts the spherical grid to Cartesian and renders a Plotly 3D surface. `App.jsx` manages a separate `radiation` state and `loadingRadiation` state.

**Tech Stack:** Python, openEMS (`FDTD.CreateNF2FFBox`, `nf2ff.CalcNF2FF`), NumPy, FastAPI, React 19, Plotly.js (`react-plotly.js`, `type: 'surface'`)

---

### Task 1: Add `with_radiation` to `dipole.py` (template)

**Files:**
- Modify: `backend/app/simulators/dipole.py`

This is the reference implementation. All other simulators follow the same pattern.

**Step 1: Read the file**

Read `backend/app/simulators/dipole.py` to understand the current structure before editing.

**Step 2: Add `with_radiation=False` to the function signature**

Change:
```python
def simulate_dipole(params: dict, conductor: ConductorParams = None) -> dict:
```
To:
```python
def simulate_dipole(params: dict, conductor: ConductorParams = None, with_radiation: bool = False) -> dict:
```

**Step 3: Create the NF2FF box before `FDTD.Run()`**

After `FDTD.SetBoundaryCond(['PML_8'] * 6)` and after all mesh/geometry setup, add immediately before `CSX.Write2XML(...)`:
```python
    if with_radiation:
        nf2ff = FDTD.CreateNF2FFBox()
```

**Step 4: Compute radiation after `FDTD.Run()` and S11, inside the `try` block**

After the existing S11 computation and before the `return` statement, add:
```python
        result = {
            "antenna_type": "dipole",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        if with_radiation:
            theta = np.linspace(0, np.pi, 37)       # 0–180°, step 5°
            phi   = np.linspace(0, 2 * np.pi, 73)  # 0–360°, step 5°
            nf2ff.CalcNF2FF(sim_dir, [f0], theta, phi)
            e_abs = np.abs(nf2ff.E_norm[0])         # shape (37, 73)
            e_max = float(e_abs.max())
            if e_max > 0:
                e_db = 20.0 * np.log10(e_abs / e_max + 1e-12)
            else:
                e_db = np.zeros_like(e_abs)
            result["results"]["radiation"] = {
                "theta_deg":       np.degrees(theta).tolist(),
                "phi_deg":         np.degrees(phi).tolist(),
                "e_norm_db":       e_db.tolist(),
                "directivity_dbi": float(np.max(nf2ff.Dmax)),
                "frequency_mhz":   float(f0 / 1e6),
            }
        return result
```

Remove the old `return { "antenna_type": ... }` statement that was there before.

**Step 5: Verify the file structure is correct**

Read the file after editing. Confirm:
- Function signature has `with_radiation: bool = False`
- `nf2ff = FDTD.CreateNF2FFBox()` is inside `if with_radiation:` BEFORE `CSX.Write2XML`
- The radiation block is inside the `try:` block, AFTER `port.CalcPort`
- The `return result` replaces the old return
- `shutil.rmtree` is still in `finally:`

**Step 6: Commit**

```bash
git -C /Users/yayoboy/Desktop/GitHub/aerials add backend/app/simulators/dipole.py
git -C /Users/yayoboy/Desktop/GitHub/aerials commit -m "feat: add with_radiation NF2FF support to dipole simulator"
```

---

### Task 2: Add `with_radiation` to all remaining 11 simulators

**Files:**
- Modify: `backend/app/simulators/folded_dipole.py`
- Modify: `backend/app/simulators/monopole.py`
- Modify: `backend/app/simulators/yagi.py`
- Modify: `backend/app/simulators/inverted_v.py`
- Modify: `backend/app/simulators/loop.py`
- Modify: `backend/app/simulators/helix.py`
- Modify: `backend/app/simulators/sleeve.py`
- Modify: `backend/app/simulators/discone.py`
- Modify: `backend/app/simulators/patch.py`
- Modify: `backend/app/simulators/ground_plane.py`
- Modify: `backend/app/simulators/jpole.py`

Apply the **exact same pattern** as Task 1 to each file. For each simulator:

1. Read the file first
2. Add `with_radiation: bool = False` to function signature
3. Add `if with_radiation: nf2ff = FDTD.CreateNF2FFBox()` before `CSX.Write2XML(...)`
4. Replace the `return { ... }` with the `result = { ... }` dict + radiation block + `return result`
5. The radiation block is **identical** in all 12 simulators — only `"antenna_type"` value changes

**The radiation block to add (identical for all, substitute correct `antenna_type` string):**
```python
        result = {
            "antenna_type": "<antenna_id>",   # e.g. "monopole", "yagi", etc.
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        if with_radiation:
            theta = np.linspace(0, np.pi, 37)
            phi   = np.linspace(0, 2 * np.pi, 73)
            nf2ff.CalcNF2FF(sim_dir, [f0], theta, phi)
            e_abs = np.abs(nf2ff.E_norm[0])
            e_max = float(e_abs.max())
            if e_max > 0:
                e_db = 20.0 * np.log10(e_abs / e_max + 1e-12)
            else:
                e_db = np.zeros_like(e_abs)
            result["results"]["radiation"] = {
                "theta_deg":       np.degrees(theta).tolist(),
                "phi_deg":         np.degrees(phi).tolist(),
                "e_norm_db":       e_db.tolist(),
                "directivity_dbi": float(np.max(nf2ff.Dmax)),
                "frequency_mhz":   float(f0 / 1e6),
            }
        return result
```

**Note on `f0` variable name:** Most simulators use `f0`. Check each file — if the frequency variable has a different name (e.g. `freq`), use that name in `nf2ff.CalcNF2FF(sim_dir, [f0], ...)` and `float(f0 / 1e6)`.

**Note on `f_eval`:** Most simulators compute S11 over `f_eval = np.linspace(...)` but the NF2FF is computed only at `f0` (center frequency, single point). This is correct — radiation pattern at the design frequency.

**Step: Commit all 11 at once**
```bash
git -C /Users/yayoboy/Desktop/GitHub/aerials add backend/app/simulators/
git -C /Users/yayoboy/Desktop/GitHub/aerials commit -m "feat: add with_radiation NF2FF support to all remaining 11 simulators"
```

---

### Task 3: Add `/radiation/{antenna_type}` endpoint to `main.py` + test

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/tests/test_api.py`

**Step 1: Add the new endpoint to `main.py`**

After the existing `/simulate/{antenna_type}` endpoint, add:
```python
@app.post("/radiation/{antenna_type}")
def run_radiation(antenna_type: str, req: SimulationRequest):
    if antenna_type not in SIMULATOR_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown antenna type: '{antenna_type}'. Available: {list(SIMULATOR_MAP.keys())}"
        )
    print(f"[radiation/{antenna_type}] params={req.antenna_params} conductor={req.conductor}")
    try:
        return SIMULATOR_MAP[antenna_type](req.antenna_params, req.conductor, with_radiation=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Add tests to `test_api.py`**

```python
def test_radiation_unknown_antenna_returns_404():
    client = get_client()
    r = client.post("/radiation/totally_unknown_xyz", json={
        "antenna_params": {},
        "conductor": {}
    })
    assert r.status_code == 404

def test_radiation_endpoint_exists():
    client = get_client()
    r = client.post("/radiation/dipole", json={
        "antenna_params": {"frequency_mhz": 300, "length_mm": 475},
        "conductor": {"material": "copper", "cross_section": "round", "radius_mm": 1.0}
    })
    # 200 (if openEMS available) or 500 (if not) — NOT 404 or 422
    assert r.status_code in (200, 500)
```

**Step 3: Run the tests**
```bash
cd /Users/yayoboy/Desktop/GitHub/aerials/backend && python -m pytest tests/test_api.py -v
```
Expected: all tests pass (the radiation endpoint tests will be 200 or 500, not 404).

**Step 4: Commit**
```bash
git -C /Users/yayoboy/Desktop/GitHub/aerials add backend/main.py backend/tests/test_api.py
git -C /Users/yayoboy/Desktop/GitHub/aerials commit -m "feat: add /radiation/{antenna_type} endpoint"
```

---

### Task 4: Create `RadiationView.jsx`

**Files:**
- Create: `frontend/src/components/RadiationView.jsx`

**Step 1: Create the component**

```jsx
// frontend/src/components/RadiationView.jsx
import Plot from 'react-plotly.js';

export default function RadiationView({ radiation }) {
  if (!radiation) return null;

  const { theta_deg, phi_deg, e_norm_db, directivity_dbi, frequency_mhz } = radiation;

  const nTheta = theta_deg.length;  // 37
  const nPhi   = phi_deg.length;    // 73

  // Spherical → Cartesian conversion
  // r = linear gain (0–1), x/y/z = r * unit sphere coords
  const X = [], Y = [], Z = [];
  for (let i = 0; i < nTheta; i++) {
    const rowX = [], rowY = [], rowZ = [];
    const tRad = theta_deg[i] * Math.PI / 180;
    for (let j = 0; j < nPhi; j++) {
      const pRad = phi_deg[j] * Math.PI / 180;
      const r    = Math.pow(10, e_norm_db[i][j] / 20);
      rowX.push(r * Math.sin(tRad) * Math.cos(pRad));
      rowY.push(r * Math.sin(tRad) * Math.sin(pRad));
      rowZ.push(r * Math.cos(tRad));
    }
    X.push(rowX);
    Y.push(rowY);
    Z.push(rowZ);
  }

  const layout = {
    autosize: true,
    paper_bgcolor: 'transparent',
    scene: {
      bgcolor: 'transparent',
      xaxis: { visible: false },
      yaxis: { visible: false },
      zaxis: { visible: false },
      aspectmode: 'data',
    },
    margin: { t: 0, r: 0, l: 0, b: 0 },
    annotations: [{
      xref: 'paper', yref: 'paper',
      x: 0.01, y: 0.01,
      text: `Dmax: ${directivity_dbi.toFixed(2)} dBi &nbsp;@&nbsp; ${frequency_mhz.toFixed(1)} MHz`,
      showarrow: false,
      font: { size: 12, color: '#8b949e' },
      bgcolor: 'rgba(13,17,23,0.6)',
      borderpad: 4,
      xanchor: 'left',
      yanchor: 'bottom',
    }],
  };

  return (
    <Plot
      data={[{
        type: 'surface',
        x: X,
        y: Y,
        z: Z,
        surfacecolor: e_norm_db,
        colorscale: 'Viridis',
        colorbar: {
          title: { text: 'dB', side: 'right' },
          thickness: 12,
          len: 0.6,
          tickfont: { color: '#8b949e', size: 10 },
          titlefont: { color: '#8b949e', size: 10 },
        },
        showscale: true,
        hovertemplate: 'dB: %{surfacecolor:.1f}<extra></extra>',
      }]}
      layout={layout}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
    />
  );
}
```

**Step 2: Verify**

Read the created file and confirm:
- Spherical to Cartesian conversion is correct (nested loop, theta outer, phi inner)
- `r = Math.pow(10, e_norm_db[i][j] / 20)` converts dB to linear (0–1)
- `layout.scene.aspectmode = 'data'` (preserves true shape)
- No imports other than `react-plotly.js`

**Step 3: Commit**
```bash
git -C /Users/yayoboy/Desktop/GitHub/aerials add frontend/src/components/RadiationView.jsx
git -C /Users/yayoboy/Desktop/GitHub/aerials commit -m "feat: RadiationView 3D surface component"
```

---

### Task 5: Update `App.jsx`

**Files:**
- Modify: `frontend/src/App.jsx`

**Step 1: Read `App.jsx` first**

Read the full file before any edit. Note the current imports, state declarations, handlers, and JSX structure.

**Step 2: Add `RadiationView` import**

At the top, after the existing component imports:
```js
import RadiationView from './components/RadiationView.jsx';
```

**Step 3: Add radiation state variables**

Inside the `App` component, after existing `useState` declarations:
```js
const [radiation,        setRadiation]        = useState(null);
const [loadingRadiation, setLoadingRadiation] = useState(false);
const [errorRadiation,   setErrorRadiation]   = useState(null);
```

**Step 4: Clear radiation on antenna change**

In `handleAntennaChange`, add `setRadiation(null)` after `setResults(null)`:
```js
const handleAntennaChange = (type) => {
  setAntennaType(type);
  setParams(ANTENNA_MAP[type].defaultParams);
  setResults(null);
  setRadiation(null);   // <-- add this
  setError(null);
};
```

**Step 5: Add `handleRadiation` handler**

After `handleSimulate`, add:
```js
const handleRadiation = async () => {
  setLoadingRadiation(true);
  setRadiation(null);
  setErrorRadiation(null);
  try {
    const res = await fetch(`http://localhost:8000/radiation/${antennaType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ antenna_params: params, conductor }),
    });
    const data = await res.json();
    if (!res.ok) {
      setErrorRadiation(data.detail ?? 'Errore calcolo radiazione');
    } else {
      setRadiation(data.results.radiation);
    }
  } catch (err) {
    setErrorRadiation(err.message);
  } finally {
    setLoadingRadiation(false);
  }
};
```

**Step 6: Add button to sidebar JSX**

In the sidebar `<aside>`, after the error `<p>` block and after `<SimHistory>`, add:
```jsx
{results && (
  <button
    className="btn-secondary"
    onClick={handleRadiation}
    disabled={loadingRadiation}
    style={{ marginTop: '8px' }}
  >
    {loadingRadiation ? 'Calcolo...' : 'Calcola diagramma'}
  </button>
)}
{errorRadiation && (
  <p style={{ color: '#f85149', marginTop: '8px', fontSize: '13px' }}>
    {errorRadiation}
  </p>
)}
```

**Step 7: Add radiation panel to main content**

In `<main className="main-content">`, after the existing S11 `glass-panel`:
```jsx
{radiation && (
  <div className="glass-panel">
    <h2 className="panel-header">
      Diagramma di Radiazione — {cfg?.label ?? antennaType}
    </h2>
    <div className="plot-container" style={{ height: '380px' }}>
      <RadiationView radiation={radiation} />
    </div>
  </div>
)}
```

**Step 8: Verify**

Read the file and confirm:
- `RadiationView` is imported
- 3 new state variables present
- `handleAntennaChange` clears `radiation`
- `handleRadiation` is present and correct
- Sidebar button only renders when `results` is non-null
- Radiation panel only renders when `radiation` is non-null

**Step 9: Commit**
```bash
git -C /Users/yayoboy/Desktop/GitHub/aerials add frontend/src/App.jsx
git -C /Users/yayoboy/Desktop/GitHub/aerials commit -m "feat: radiation button and 3D panel in App"
```

---

### Task 6: Final verification

**Step 1: Run backend tests**
```bash
cd /Users/yayoboy/Desktop/GitHub/aerials/backend && python -m pytest tests/ -v
```
Expected: all tests pass.

**Step 2: Check frontend builds without errors**
```bash
cd /Users/yayoboy/Desktop/GitHub/aerials/frontend && npm run build
```
Expected: build succeeds, no import errors.

**Step 3: Manual smoke test (requires Docker)**

Start the stack:
```bash
cd /Users/yayoboy/Desktop/GitHub/aerials && docker compose up -d
cd frontend && npm run dev
```

Test checklist:
- [ ] `[Calcola diagramma]` button NOT visible before simulation
- [ ] Run a dipole simulation → `[Calcola diagramma]` appears
- [ ] Click `[Calcola diagramma]` → loading state, then 3D surface appears
- [ ] 3D surface is interactive (rotate, zoom)
- [ ] Dmax annotation visible (e.g. "Dmax: 2.15 dBi @ 300.0 MHz")
- [ ] Change antenna type → radiation panel disappears
- [ ] Run simulation for yagi → radiation shows directional beam
- [ ] Error shown if backend returns 500

**Step 4: Commit any fixes found**
```bash
git -C /Users/yayoboy/Desktop/GitHub/aerials add -p
git -C /Users/yayoboy/Desktop/GitHub/aerials commit -m "fix: <describe fix>"
```
