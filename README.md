# Aerials

A full-stack antenna simulation web app powered by openEMS FDTD — design, simulate, and visualize **21 antenna types** with S11 return loss plots, 2D polar diagrams and interactive 3D radiation patterns.

## Stack

- **Backend**: Python, FastAPI, openEMS (FDTD), Pydantic v2
- **Frontend**: React 19, Vite, Three.js, Plotly.js
- **Infrastructure**: Docker, Docker Compose

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)

No other dependencies are required. Everything runs inside containers.

## Quick Start

```bash
git clone https://github.com/yayoboy/aerials.git
cd aerials
docker compose up
```

> **Note:** The first build compiles openEMS from source and can take **30–60 minutes**. Subsequent builds use the Docker layer cache and start in seconds.

Once running, open your browser:

| Service          | URL                          |
|------------------|------------------------------|
| Frontend         | http://localhost:5173        |
| Backend API      | http://localhost:8000        |
| Swagger UI       | http://localhost:8000/docs   |

## Supported Antenna Types

| # | ID | Label | Notes |
|---|----|-------|-------|
| 1 | `dipole` | Dipolo λ/2 | Half-wave dipole |
| 2 | `folded_dipole` | Dipolo Ripiegato | 300 Ω feed impedance |
| 3 | `monopole` | Monopolo λ/4 | Quarter-wave over ground plane |
| 4 | `yagi` | Yagi-Uda | Directional, configurable directors |
| 5 | `inverted_v` | Inverted V | Wire dipole with apex angle |
| 6 | `loop` | Loop | Square loop |
| 7 | `helix` | Elica | Axial or normal mode |
| 8 | `sleeve` | Sleeve Monopole | Coaxial sleeve variant |
| 9 | `discone` | Discone | Wideband, VHF/UHF |
| 10 | `patch` | Patch (Microstrip) | Substrate configurable |
| 11 | `ground_plane` | Ground Plane | Configurable radials |
| 12 | `jpole` | J-Pole | Omnidirectional |
| 13 | `moxon` | Moxon | Compact directional |
| 14 | `turnstile` | Turnstile | Two crossed dipoles, elliptical polarisation |
| 15 | `collinear` | Array Collineare | N stacked half-wave elements, horizon gain |
| 16 | `efhw` | EFHW | End-fed half-wave, 2450 Ω port (49:1 UNUN) |
| 17 | `lpda` | LPDA | Log-periodic dipole array, broadband |
| 18 | `biconical` | Biconica | Dual-cone, wideband EMC |
| 19 | `rhombic` | Rombica | Diamond wire + 600 Ω termination, HF |
| 20 | `cloverleaf` | Cloverleaf | 3 tilted loops, circular polarisation FPV |
| 21 | `vivaldi` | Vivaldi (TSA) | Exponential tapered slot, UWB end-fire |

## Features

- **FDTD simulation** via openEMS for each antenna type
- **S11 return loss** plot (frequency sweep ±20 % around design frequency)
- **2D polar radiation diagram** — E-plane, H-plane, and optional azimuth cut
- **3D radiation pattern** — interactive rotatable surface (toggle 2D/3D)
- **Conductor selection** — Copper, Silver, Aluminium, Steel, Brass or custom; round, tube, flat or square cross-section
- **Result caching** — LRU cache (128 entries) for instant replay of identical simulations
- **Feed impedance awareness** — each antenna's port is normalised to its physical feed impedance (50 Ω for most; 300 Ω for folded dipole; 2450 Ω for EFHW)

## Useful Commands

| Command                                  | Description                              |
|------------------------------------------|------------------------------------------|
| `docker compose up`                      | Start all services (foreground, live logs) |
| `docker compose up -d`                   | Start all services (detached/background) |
| `docker compose down`                    | Stop and remove containers               |
| `docker compose build`                   | Rebuild images without starting          |
| `docker compose logs backend`            | Tail backend logs                        |
| `docker compose logs frontend`           | Tail frontend logs                       |

## Development

### Hot Reload

Both services support hot reload out of the box:

- **Frontend**: Vite watches `frontend/src/` — any saved change reloads the browser instantly.
- **Backend**: Uvicorn runs with `--reload` — any saved change to `backend/` restarts the server automatically.

No container restart is needed during normal development.

### Project Structure

```
aerials/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── main.py                  # FastAPI app + SIMULATOR_MAP (21 entries)
│   ├── requirements.txt
│   └── app/
│       ├── conductor.py         # ConductorMaterial, CrossSection, ConductorParams
│       ├── models.py            # 21 antenna Pydantic models + SimulationRequest
│       ├── sim_utils.py         # Shared FDTD helpers (mesh, NrTS, NF2FF sampling)
│       └── simulators/          # One FDTD simulator module per antenna type
│           ├── dipole.py
│           ├── folded_dipole.py
│           ├── monopole.py
│           ├── yagi.py
│           ├── inverted_v.py
│           ├── loop.py
│           ├── helix.py
│           ├── sleeve.py
│           ├── discone.py
│           ├── patch.py
│           ├── ground_plane.py
│           ├── jpole.py
│           ├── moxon.py
│           ├── turnstile.py
│           ├── collinear.py
│           ├── efhw.py
│           ├── lpda.py
│           ├── biconical.py
│           ├── rhombic.py
│           ├── cloverleaf.py
│           └── vivaldi.py
└── frontend/
    ├── src/
    │   ├── App.jsx              # Root component, wires all pieces together
    │   ├── components/
    │   │   ├── AntennaSelector.jsx
    │   │   ├── AntennaForm.jsx
    │   │   ├── ConductorForm.jsx
    │   │   ├── S11Chart.jsx
    │   │   ├── Antenna3DView.jsx
    │   │   └── RadiationChart.jsx  # 2D polar + 3D surface (toggle)
    │   ├── antennas/
    │   │   ├── configs/         # Per-antenna config (id, label, defaultParams, fields, derivedFromFreq)
    │   │   └── geometries/      # Three.js buildX() functions per antenna
    │   └── constants/
    │       └── conductors.js    # MATERIALS, CROSS_SECTIONS
    └── ...
```

### Adding a New Simulator

1. **Create the simulator** at `backend/app/simulators/<name>.py`:

   ```python
   def simulate_<name>(params: dict, conductor, with_radiation=False) -> dict:
       # Run openEMS FDTD simulation
       return {
           "antenna_type": "<name>",
           "status": "success",
           "results": {
               "frequencies_mhz": [...],
               "s11_db": [...],
           },
       }
   ```

2. **Add a Pydantic model** in `backend/app/models.py`:

   ```python
   class <Name>Params(BaseModel):
       frequency_mhz: float = 300.0
       # ... antenna-specific parameters
   ```

3. **Register the simulator** in `backend/main.py` inside `_load_simulators()`:

   ```python
   from app.simulators.<name> import simulate_<name>
   simulators["<name>"] = simulate_<name>
   ```

4. **Add frontend config** at `frontend/src/antennas/configs/<name>.js` exporting an object with `id`, `label`, `description`, `defaultParams`, `derivedFromFreq()` and `fields`.

5. **Add 3D geometry** at `frontend/src/antennas/geometries/<name>.js` exporting `build<Name>(params, conductor, color)` returning a `THREE.Group`.

6. **Register both** in `frontend/src/antennas/configs/index.js` and `frontend/src/antennas/geometries/index.js`.

### Running Backend Tests

```bash
docker compose exec backend python -m pytest tests/ -v
```

## API

| Method | Endpoint                        | Description                                  |
|--------|---------------------------------|----------------------------------------------|
| GET    | `/`                             | Health check + list of loaded simulators     |
| POST   | `/simulate/{antenna_type}`      | Run FDTD simulation for the specified antenna |
| GET    | `/cache`                        | Cache statistics (size, hit rate)            |
| POST   | `/cache/clear`                  | Flush the simulation result cache            |

**Request body** (`POST /simulate/{antenna_type}`):

```json
{
  "antenna_params": { "frequency_mhz": 144, "arm_length_mm": 510 },
  "conductor": { "material": "copper", "cross_section": "round", "radius_mm": 1.0 },
  "with_radiation": false
}
```

Full interactive API documentation is available at **http://localhost:8000/docs** when the stack is running.
