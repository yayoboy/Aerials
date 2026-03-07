# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import SimulationRequest

def _load_simulators():
    simulators = {}

    try:
        from app.simulators.dipole import simulate_dipole
        simulators["dipole"] = simulate_dipole
    except ImportError:
        pass

    try:
        from app.simulators.folded_dipole import simulate_folded_dipole
        simulators["folded_dipole"] = simulate_folded_dipole
    except ImportError:
        pass

    try:
        from app.simulators.monopole import simulate_monopole
        simulators["monopole"] = simulate_monopole
    except ImportError:
        pass

    try:
        from app.simulators.yagi import simulate_yagi
        simulators["yagi"] = simulate_yagi
    except ImportError:
        pass

    try:
        from app.simulators.inverted_v import simulate_inverted_v
        simulators["inverted_v"] = simulate_inverted_v
    except ImportError:
        pass

    try:
        from app.simulators.loop import simulate_loop
        simulators["loop"] = simulate_loop
    except ImportError:
        pass

    try:
        from app.simulators.helix import simulate_helix
        simulators["helix"] = simulate_helix
    except ImportError:
        pass

    try:
        from app.simulators.sleeve import simulate_sleeve
        simulators["sleeve"] = simulate_sleeve
    except ImportError:
        pass

    try:
        from app.simulators.discone import simulate_discone
        simulators["discone"] = simulate_discone
    except ImportError:
        pass

    try:
        from app.simulators.patch import simulate_patch
        simulators["patch"] = simulate_patch
    except ImportError:
        pass

    try:
        from app.simulators.ground_plane import simulate_ground_plane
        simulators["ground_plane"] = simulate_ground_plane
    except ImportError:
        pass

    try:
        from app.simulators.jpole import simulate_jpole
        simulators["jpole"] = simulate_jpole
    except ImportError:
        pass

    return simulators

SIMULATOR_MAP = _load_simulators()

app = FastAPI(title="Aerials — Antenna Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "antennas": list(SIMULATOR_MAP.keys())}

@app.post("/simulate/{antenna_type}")
def run_simulation(antenna_type: str, req: SimulationRequest):
    if antenna_type not in SIMULATOR_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown antenna type: '{antenna_type}'. Available: {list(SIMULATOR_MAP.keys())}"
        )
    print(f"[{antenna_type}] params={req.antenna_params} conductor={req.conductor}")
    try:
        return SIMULATOR_MAP[antenna_type](req.antenna_params, req.conductor)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
