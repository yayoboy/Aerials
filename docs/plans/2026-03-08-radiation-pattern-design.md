# Design: 3D Radiation Pattern Diagram

**Date:** 2026-03-08
**Status:** Approved

## Goal

Add a 3D radiation pattern visualization computed via openEMS FDTD near-to-far-field (NF2FF) transform, displayed as an interactive Plotly 3D surface plot.

## User Flow

1. User configures antenna parameters and clicks **[Avvia simulazione FDTD]** → S11 chart appears (existing)
2. A new button **[Calcola diagramma]** becomes active in the sidebar (only after results are available)
3. User clicks it → loading state, request to `/radiation/{antenna_type}`
4. Response arrives → new panel appears below S11 chart with the 3D radiation surface + directivity

## Architecture

### Backend — `with_radiation` flag

Each of the 12 simulator functions gains an optional `with_radiation: bool = False` parameter. When `True`:

1. Before `FDTD.Run()`, add: `nf2ff = FDTD.CreateNF2FFBox()`
2. After `FDTD.Run()`, compute:
   ```python
   theta = np.linspace(0, np.pi, 37)      # 0°–180°, 5° step
   phi   = np.linspace(0, 2*np.pi, 73)    # 0°–360°, 5° step
   nf2ff.CalcNF2FF(sim_dir, [f0], theta, phi)
   e_norm = nf2ff.E_norm[0]               # shape (37, 73), complex
   e_abs  = np.abs(e_norm)
   e_db   = 20 * np.log10(e_abs / e_abs.max() + 1e-12)  # normalized, max=0 dB
   directivity = float(nf2ff.Dmax[0])    # dBi
   ```
3. Add to `results`:
   ```python
   "radiation": {
       "theta_deg":       (np.degrees(theta)).tolist(),   # shape (37,)
       "phi_deg":         (np.degrees(phi)).tolist(),     # shape (73,)
       "e_norm_db":       e_db.tolist(),                  # shape (37, 73)
       "directivity_dbi": directivity,
       "frequency_mhz":   float(f0 / 1e6),
   }
   ```

### Backend — New Endpoint

```python
@app.post("/radiation/{antenna_type}")
def run_radiation(antenna_type: str, req: SimulationRequest):
    simulator = SIMULATOR_MAP.get(antenna_type)
    if not simulator:
        raise HTTPException(404, detail=f"Unknown: {antenna_type}")
    try:
        return simulator(req.antenna_params, req.conductor, with_radiation=True)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
```

### Frontend — State (`App.jsx`)

New state variables:
```js
const [radiation,        setRadiation]        = useState(null);
const [loadingRadiation, setLoadingRadiation] = useState(false);
const [errorRadiation,   setErrorRadiation]   = useState(null);
```

Handler `handleRadiation()`:
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
    if (!res.ok) setErrorRadiation(data.detail ?? 'Errore');
    else setRadiation(data.results.radiation);
  } catch (err) {
    setErrorRadiation(err.message);
  } finally {
    setLoadingRadiation(false);
  }
};
```

Button in sidebar (after simulate button, only when `results` is non-null):
```jsx
{results && (
  <button className="btn-secondary" onClick={handleRadiation} disabled={loadingRadiation}>
    {loadingRadiation ? 'Calcolo...' : 'Calcola diagramma'}
  </button>
)}
```

Clear radiation when antenna type or params change (in `handleAntennaChange` and optionally on simulate).

### Frontend — `RadiationView.jsx`

Converts spherical → Cartesian for Plotly surface:
```js
// r = linear gain (0–1), normalized
const r = e_norm_linear[i][j];
X[i][j] = r * Math.sin(theta_rad[i]) * Math.cos(phi_rad[j]);
Y[i][j] = r * Math.sin(theta_rad[i]) * Math.sin(phi_rad[j]);
Z[i][j] = r * Math.cos(theta_rad[i]);
```

Where `e_norm_linear[i][j] = Math.pow(10, e_norm_db[i][j] / 20)`.

Plotly trace:
```js
{
  type: 'surface',
  x: X, y: Y, z: Z,
  surfacecolor: e_norm_db,   // color = gain in dB
  colorscale: 'Viridis',
  colorbar: { title: 'dB', thickness: 12 },
  showscale: true,
}
```

Layout: dark background, no axes tick labels, equal aspect ratio, `scene.aspectmode: 'data'`.

Annotation row below chart: `Dmax: {directivity_dbi.toFixed(2)} dBi @ {frequency_mhz.toFixed(1)} MHz`.

### Frontend — Panel Layout (`App.jsx`)

New `glass-panel` in `main-content`, below the S11 panel:
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

## Files Changed

| File | Change |
|------|--------|
| `backend/app/simulators/dipole.py` | Add `with_radiation=False`, NF2FF block |
| `backend/app/simulators/folded_dipole.py` | Same |
| `backend/app/simulators/monopole.py` | Same |
| `backend/app/simulators/yagi.py` | Same |
| `backend/app/simulators/inverted_v.py` | Same |
| `backend/app/simulators/loop.py` | Same |
| `backend/app/simulators/helix.py` | Same |
| `backend/app/simulators/sleeve.py` | Same |
| `backend/app/simulators/discone.py` | Same |
| `backend/app/simulators/patch.py` | Same |
| `backend/app/simulators/ground_plane.py` | Same |
| `backend/app/simulators/jpole.py` | Same |
| `backend/main.py` | New `/radiation/{antenna_type}` endpoint |
| `frontend/src/App.jsx` | Radiation state, handler, button, panel |
| `frontend/src/components/RadiationView.jsx` | New Plotly 3D surface component |

## NF2FF Grid Resolution

- theta: 37 points (0°–180°, step 5°)
- phi: 73 points (0°–360°, step 5°)
- Total surface points: 37 × 73 = 2,701 (lightweight for Plotly)

## Error Handling

- If NF2FF fails (e.g. field values too small), backend logs and raises 500
- Frontend shows `errorRadiation` message below the radiation button
- S11 simulation is completely unaffected (separate endpoint)

## Notes

- NF2FF transform requires PML boundaries — all 12 simulators already use `['PML_8'] * 6`
- The NF2FF box must be placed inside the FDTD domain before `Run()` — `CreateNF2FFBox()` handles this automatically
- Radiation is cleared (`setRadiation(null)`) when antenna type changes via `handleAntennaChange`
