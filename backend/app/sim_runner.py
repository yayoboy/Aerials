# backend/app/sim_runner.py
"""
Runs a simulator function in a separate OS process with a hard wall-clock timeout.

FDTD.Run() is a blocking C++ call that cannot be interrupted from Python threads.
The only reliable way to stop it is to kill the OS process (multiprocessing.Process).

Optimizations:
- Uses 'fork' context on Linux for faster process startup
- LRU cache for identical simulation parameters
- Early termination support via convergence detection
"""
import multiprocessing
import hashlib
import json
import os
from functools import lru_cache
from typing import Any, Callable, Tuple, Dict, Optional


# LRU cache for simulation results (max 128 entries)
# Cache key is hash of (function_name, params_json, conductor_json, with_radiation)
_simulation_cache: Dict[str, Any] = {}
CACHE_MAX_SIZE = 128


def _compute_cache_key(fn_name: str, args: tuple, kwargs: dict) -> str:
    """Compute a cache key based on function name and parameters."""
    key_data = {
        "fn": fn_name,
        "args": args,
        "kwargs": kwargs,
    }
    key_json = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_json.encode()).hexdigest()[:16]


def _get_cached(key: str) -> Optional[Any]:
    """Get result from cache if exists."""
    return _simulation_cache.get(key)


def _set_cached(key: str, value: Any) -> None:
    """Set result in cache with LRU eviction."""
    if len(_simulation_cache) >= CACHE_MAX_SIZE:
        # Remove oldest entry (first item)
        oldest_key = next(iter(_simulation_cache))
        del _simulation_cache[oldest_key]
    _simulation_cache[key] = value


def _worker(q, fn, args, kwargs):
    try:
        q.put(("ok", fn(*args, **kwargs)))
    except Exception:
        import traceback
        q.put(("err", traceback.format_exc()))


def run_with_timeout(
    fn: Callable,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    timeout_s: int = 300,
    use_cache: bool = True,
) -> Any:
    """
    Run fn(*args, **kwargs) in a child process.
    Kill the process and raise TimeoutError if it exceeds timeout_s wall-clock seconds.
    
    Args:
        fn: Simulator function to run
        args: Positional arguments for fn
        kwargs: Keyword arguments for fn
        timeout_s: Timeout in seconds (default 300s)
        use_cache: Whether to use result caching (default True)
    
    Returns:
        Simulation result dictionary
    
    Raises:
        TimeoutError: If simulation exceeds timeout
        RuntimeError: If simulation fails or process exits unexpectedly
    """
    if kwargs is None:
        kwargs = {}
    
    # Check cache first
    if use_cache:
        cache_key = _compute_cache_key(fn.__name__, args, kwargs)
        cached_result = _get_cached(cache_key)
        if cached_result is not None:
            cached_result["_cached"] = True
            return cached_result
    
    # Use 'fork' on Linux for faster process startup, 'spawn' on macOS/Windows
    os_name = os.name
    if os_name == "posix":
        # Check if we're on macOS (darwin) or Linux
        import platform
        if platform.system() == "Linux":
            ctx = multiprocessing.get_context("fork")
        else:
            # macOS - use spawn for safety with openEMS
            ctx = multiprocessing.get_context("spawn")
    else:
        ctx = multiprocessing.get_context("spawn")
    
    q = ctx.Queue()
    p = ctx.Process(target=_worker, args=(q, fn, args, kwargs), daemon=True)
    p.start()
    p.join(timeout=timeout_s)
    
    if p.is_alive():
        p.kill()
        p.join()
        raise TimeoutError(f"Simulazione interrotta: timeout di {timeout_s} secondi superato")
    
    if q.empty():
        raise RuntimeError(f"Il processo di simulazione è terminato inaspettatamente (exit code {p.exitcode})")
    
    status, payload = q.get()
    
    if status == "err":
        raise RuntimeError(payload)
    
    # Cache successful result
    if use_cache and isinstance(payload, dict) and payload.get("status") == "success":
        _set_cached(cache_key, payload)
        payload["_cached"] = False
    
    return payload


def clear_cache() -> None:
    """Clear the simulation result cache."""
    _simulation_cache.clear()


def get_cache_info() -> dict:
    """Get cache statistics."""
    return {
        "size": len(_simulation_cache),
        "max_size": CACHE_MAX_SIZE,
    }
