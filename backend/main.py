# backend/main.py
"""
Aerials - Antenna Simulator API

Optimized for performance with:
- Execution time logging and SLO monitoring
- Cache status reporting
- Configurable timeouts with warnings
"""
import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import SimulationRequest
from app.sim_runner import run_with_timeout, get_cache_info, clear_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aerials")

# SLO thresholds
SLO_WARNING_MS = 300_000  # 300s - log warning
SLO_CRITICAL_MS = 500_000  # 500s - log critical
DEFAULT_TIMEOUT_S = 600  # 10 minutes total timeout


def _load_simulators():
    simulators = {}

    try:
        from app.simulators.dipole import simulate_dipole
        simulators["dipole"] = simulate_dipole
    except ImportError as e:
        logger.warning(f"Could not load dipole simulator: {e}")

    try:
        from app.simulators.folded_dipole import simulate_folded_dipole
        simulators["folded_dipole"] = simulate_folded_dipole
    except ImportError as e:
        logger.warning(f"Could not load folded_dipole simulator: {e}")

    try:
        from app.simulators.monopole import simulate_monopole
        simulators["monopole"] = simulate_monopole
    except ImportError as e:
        logger.warning(f"Could not load monopole simulator: {e}")

    try:
        from app.simulators.yagi import simulate_yagi
        simulators["yagi"] = simulate_yagi
    except ImportError as e:
        logger.warning(f"Could not load yagi simulator: {e}")

    try:
        from app.simulators.inverted_v import simulate_inverted_v
        simulators["inverted_v"] = simulate_inverted_v
    except ImportError as e:
        logger.warning(f"Could not load inverted_v simulator: {e}")

    try:
        from app.simulators.loop import simulate_loop
        simulators["loop"] = simulate_loop
    except ImportError as e:
        logger.warning(f"Could not load loop simulator: {e}")

    try:
        from app.simulators.helix import simulate_helix
        simulators["helix"] = simulate_helix
    except ImportError as e:
        logger.warning(f"Could not load helix simulator: {e}")

    try:
        from app.simulators.sleeve import simulate_sleeve
        simulators["sleeve"] = simulate_sleeve
    except ImportError as e:
        logger.warning(f"Could not load sleeve simulator: {e}")

    try:
        from app.simulators.discone import simulate_discone
        simulators["discone"] = simulate_discone
    except ImportError as e:
        logger.warning(f"Could not load discone simulator: {e}")

    try:
        from app.simulators.patch import simulate_patch
        simulators["patch"] = simulate_patch
    except ImportError as e:
        logger.warning(f"Could not load patch simulator: {e}")

    try:
        from app.simulators.ground_plane import simulate_ground_plane
        simulators["ground_plane"] = simulate_ground_plane
    except ImportError as e:
        logger.warning(f"Could not load ground_plane simulator: {e}")

    try:
        from app.simulators.jpole import simulate_jpole
        simulators["jpole"] = simulate_jpole
    except ImportError as e:
        logger.warning(f"Could not load jpole simulator: {e}")

    try:
        from app.simulators.moxon import simulate_moxon
        simulators["moxon"] = simulate_moxon
    except ImportError as e:
        logger.warning(f"Could not load moxon simulator: {e}")

    try:
        from app.simulators.turnstile import simulate_turnstile
        simulators["turnstile"] = simulate_turnstile
    except ImportError as e:
        logger.warning(f"Could not load turnstile simulator: {e}")

    try:
        from app.simulators.collinear import simulate_collinear
        simulators["collinear"] = simulate_collinear
    except ImportError as e:
        logger.warning(f"Could not load collinear simulator: {e}")

    try:
        from app.simulators.efhw import simulate_efhw
        simulators["efhw"] = simulate_efhw
    except ImportError as e:
        logger.warning(f"Could not load efhw simulator: {e}")

    try:
        from app.simulators.lpda import simulate_lpda
        simulators["lpda"] = simulate_lpda
    except ImportError as e:
        logger.warning(f"Could not load lpda simulator: {e}")

    try:
        from app.simulators.biconical import simulate_biconical
        simulators["biconical"] = simulate_biconical
    except ImportError as e:
        logger.warning(f"Could not load biconical simulator: {e}")

    try:
        from app.simulators.rhombic import simulate_rhombic
        simulators["rhombic"] = simulate_rhombic
    except ImportError as e:
        logger.warning(f"Could not load rhombic simulator: {e}")

    try:
        from app.simulators.cloverleaf import simulate_cloverleaf
        simulators["cloverleaf"] = simulate_cloverleaf
    except ImportError as e:
        logger.warning(f"Could not load cloverleaf simulator: {e}")

    try:
        from app.simulators.vivaldi import simulate_vivaldi
        simulators["vivaldi"] = simulate_vivaldi
    except ImportError as e:
        logger.warning(f"Could not load vivaldi simulator: {e}")

    logger.info(f"Loaded {len(simulators)}/21 simulators: {list(simulators.keys())}")
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


@app.get("/cache")
def cache_status():
    """Get cache statistics."""
    return get_cache_info()


@app.post("/cache/clear")
def clear_simulation_cache():
    """Clear the simulation result cache."""
    clear_cache()
    return {"status": "ok", "message": "Cache cleared"}


@app.post("/simulate/{antenna_type}")
def run_simulation(antenna_type: str, req: SimulationRequest):
    if antenna_type not in SIMULATOR_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown antenna type: '{antenna_type}'. Available: {list(SIMULATOR_MAP.keys())}"
        )
    
    logger.info(
        f"[{antenna_type}] params={req.antenna_params} "
        f"conductor={req.conductor} radiation={req.with_radiation}"
    )
    
    start_time = time.time()
    
    try:
        result = run_with_timeout(
            SIMULATOR_MAP[antenna_type],
            args=(req.antenna_params, req.conductor),
            kwargs={"with_radiation": req.with_radiation},
            timeout_s=DEFAULT_TIMEOUT_S,
            use_cache=True,
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        elapsed_s = elapsed_ms / 1000
        
        # Add performance metadata to result
        if isinstance(result, dict):
            result["performance"] = {
                "execution_time_ms": round(elapsed_ms, 2),
                "execution_time_s": round(elapsed_s, 3),
            }
        
        # Log performance with SLO monitoring
        if elapsed_ms >= SLO_CRITICAL_MS:
            logger.critical(
                f"[{antenna_type}] CRITICAL: Execution time {elapsed_s:.2f}s "
                f"exceeds critical SLO ({SLO_CRITICAL_MS/1000:.0f}s)"
            )
        elif elapsed_ms >= SLO_WARNING_MS:
            logger.warning(
                f"[{antenna_type}] WARNING: Execution time {elapsed_s:.2f}s "
                f"exceeds warning threshold ({SLO_WARNING_MS/1000:.0f}s)"
            )
        else:
            logger.info(f"[{antenna_type}] Completed in {elapsed_s:.2f}s")
        
        return result
    
    except TimeoutError as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"[{antenna_type}] Timeout after {elapsed_ms/1000:.2f}s: {e}")
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        import traceback
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"[{antenna_type}] Error after {elapsed_ms/1000:.2f}s: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
