# Aerials

A full-stack antenna simulation web app powered by openEMS FDTD — design, simulate, and visualize 12 antenna types with S11 return loss plots and interactive 3D views.

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
│   ├── main.py                  # FastAPI app + SIMULATOR_MAP
│   ├── requirements.txt
│   ├── app/
│   │   ├── conductor.py         # ConductorMaterial, CrossSection, ConductorParams
│   │   ├── models.py            # 12 antenna Pydantic models + SimulationRequest
│   │   └── simulators/          # One FDTD simulator module per antenna type
│   │       ├── dipole.py
│   │       ├── folded_dipole.py
│   │       ├── monopole.py
│   │       ├── yagi.py
│   │       ├── inverted_v.py
│   │       ├── loop.py
│   │       ├── helix.py
│   │       ├── sleeve.py
│   │       ├── discone.py
│   │       ├── patch.py
│   │       ├── ground_plane.py
│   │       └── jpole.py
│   └── tests/                   # pytest unit tests
└── frontend/
    ├── src/
    │   ├── App.jsx              # Root component, wires all pieces together
    │   ├── components/          # AntennaSelector, AntennaForm, ConductorForm, S11Chart, Antenna3DView
    │   ├── antennas/
    │   │   ├── configs/         # Per-antenna config (id, label, defaultParams, fields)
    │   │   └── geometries/      # Three.js buildX() functions per antenna
    │   └── constants/
    │       └── conductors.js    # MATERIALS, CROSS_SECTIONS
    └── ...
```

### Adding a New Simulator

1. **Create the simulator** at `backend/app/simulators/<name>.py`:

   ```python
   def simulate_<name>(params: dict, conductor) -> dict:
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

2. **Register the model** in `backend/app/models.py` — add a Pydantic model for your antenna's parameters and include it in `SimulationRequest`.

3. **Register the simulator** in `backend/main.py` — add an entry to `SIMULATOR_MAP`:

   ```python
   SIMULATOR_MAP = {
       ...
       "<name>": ("app.simulators.<name>", "simulate_<name>"),
   }
   ```

4. **Add frontend config** at `frontend/src/antennas/configs/<name>.js` with `id`, `label`, `defaultParams`, and `fields`.

5. **Add 3D geometry** at `frontend/src/antennas/geometries/<name>.js` exporting a `build<Name>(params)` function that returns a `THREE.Group`.

### Running Backend Tests

```bash
docker compose exec backend python -m pytest tests/ -v
```

## API

| Method | Endpoint                        | Description                                  |
|--------|---------------------------------|----------------------------------------------|
| GET    | `/`                             | Health check — returns `{"status": "ok"}`    |
| POST   | `/simulate/{antenna_type}`      | Run FDTD simulation for the specified antenna |

**Supported `antenna_type` values:** `dipole`, `folded_dipole`, `monopole`, `yagi`, `inverted_v`, `loop`, `helix`, `sleeve`, `discone`, `patch`, `ground_plane`, `jpole`

Full interactive API documentation (including request/response schemas and a try-it-out console) is available at **http://localhost:8000/docs** when the stack is running.
