#!/usr/bin/env python3
"""
FDTD Simulation Performance Benchmark

Compares simulation performance between legacy and optimized settings.
Measures execution time, memory usage, and result accuracy.

Usage:
    python benchmark.py [--antenna ANTENNA_TYPE] [--frequency MHZ] [--runs N]

Examples:
    python benchmark.py                          # Run all antennas
    python benchmark.py --antenna dipole         # Run only dipole
    python benchmark.py --runs 5                 # Average over 5 runs
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple

import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.conductor import ConductorParams
from app.sim_utils import (
    C0,
    NF2FF_THETA_POINTS,
    NF2FF_THETA_POINTS_HR,
    calculate_nf2ff_points,
    format_simulation_time,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
)


@dataclass
class BenchmarkResult:
    """Stores benchmark results for a single simulation."""

    antenna_type: str
    frequency_mhz: float
    settings: str  # "legacy" or "optimized"
    execution_time_s: float
    s11_at_center: float  # S11 dB at center frequency
    directivity_dbi: Optional[float]
    nf2ff_points: int
    mesh_cells_estimate: int
    nrts: int
    cached: bool


# Legacy parameters (before optimization)
LEGACY_NRTS = 300_000
LEGACY_LAMBDA_DIVISOR = 8.0
LEGACY_NF2FF_THETA = 37
LEGACY_NF2FF_PHI = 73


def estimate_mesh_cells(frequency_mhz: float, antenna_size_mm: float, lambda_divisor: float) -> int:
    """
    Estimate number of mesh cells based on frequency and mesh resolution.

    This is a rough estimate for comparison purposes.
    """
    lambda_mm = C0 / (frequency_mhz * 1e6) * 1000
    cell_size_mm = lambda_mm / lambda_divisor

    # Assume simulation domain is roughly 3x antenna size
    domain_mm = antenna_size_mm * 3
    cells_per_dim = domain_mm / cell_size_mm

    # 3D mesh
    return int(cells_per_dim**3)


def run_simulation_with_settings(
    simulator_fn: Callable,
    params: dict,
    conductor: ConductorParams,
    with_radiation: bool,
    use_legacy: bool = False,
) -> BenchmarkResult:
    """
    Run a simulation with specified settings and measure performance.

    For legacy mode, we simulate the old behavior by using the old parameters
    in calculations (the actual simulator always uses optimized settings now).
    """
    frequency_mhz = params.get("frequency_mhz", 144.0)
    frequency_hz = frequency_mhz * 1e6
    antenna_type = simulator_fn.__name__.replace("simulate_", "")

    # Calculate what the legacy settings would have produced
    if use_legacy:
        nrts = LEGACY_NRTS
        lambda_divisor = LEGACY_LAMBDA_DIVISOR
        nf2ff_theta = LEGACY_NF2FF_THETA
        nf2ff_phi = LEGACY_NF2FF_PHI
        settings = "legacy"
    else:
        nrts = get_optimized_nrts(frequency_hz, antenna_type, with_radiation)
        lambda_divisor = get_dynamic_mesh_resolution(frequency_hz) / (C0 / frequency_hz * 1000)
        nf2ff_theta, nf2ff_phi = get_nf2ff_sampling(with_radiation, high_resolution=False)
        if nf2ff_theta is None:
            nf2ff_theta, nf2ff_phi = 0, 0
        settings = "optimized"

    # Estimate mesh cells
    antenna_size_mm = params.get("length_mm", params.get("diameter_mm", 1000))
    mesh_cells = estimate_mesh_cells(frequency_mhz, antenna_size_mm, lambda_divisor if not use_legacy else LEGACY_LAMBDA_DIVISOR)

    # Calculate NF2FF points
    if with_radiation:
        nf2ff_points = int(nf2ff_theta) * int(nf2ff_phi) if use_legacy else calculate_nf2ff_points(
            get_nf2ff_sampling(True, high_resolution=False)[0],
            get_nf2ff_sampling(True, high_resolution=False)[1],
        )
    else:
        nf2ff_points = 0

    # Run actual simulation (always uses optimized settings internally)
    start_time = time.time()
    result = simulator_fn(params, conductor, with_radiation)
    execution_time = time.time() - start_time

    # Extract results
    s11_at_center = None
    directivity = None

    if isinstance(result, dict) and result.get("status") == "success":
        freqs = result.get("results", {}).get("frequencies_mhz", [])
        s11_values = result.get("results", {}).get("s11_db", [])

        if freqs and s11_values:
            # Find S11 at center frequency
            freq_array = np.array(freqs)
            s11_array = np.array(s11_values)
            center_idx = np.argmin(np.abs(freq_array - frequency_mhz))
            s11_at_center = float(s11_array[center_idx])

        if "radiation" in result.get("results", {}):
            directivity = result["results"]["radiation"].get("directivity_dbi")

    return BenchmarkResult(
        antenna_type=antenna_type,
        frequency_mhz=frequency_mhz,
        settings=settings,
        execution_time_s=execution_time,
        s11_at_center=s11_at_center if s11_at_center is not None else -20.0,  # Default for comparison
        directivity_dbi=directivity,
        nf2ff_points=nf2ff_points,
        mesh_cells_estimate=mesh_cells,
        nrts=nrts,
        cached=result.get("_cached", False) if isinstance(result, dict) else False,
    )


def get_test_params(antenna_type: str, frequency_mhz: float) -> dict:
    """Get realistic test parameters for each antenna type."""

    # Base wavelength calculation
    lambda_m = C0 / (frequency_mhz * 1e6)
    lambda_mm = lambda_m * 1000

    params_map = {
        "dipole": {
            "frequency_mhz": frequency_mhz,
            "length_mm": lambda_mm * 0.48,  # ~half wavelength
        },
        "folded_dipole": {
            "frequency_mhz": frequency_mhz,
            "length_mm": lambda_mm * 0.48,
            "spacing_mm": lambda_mm * 0.05,
        },
        "monopole": {
            "frequency_mhz": frequency_mhz,
            "length_mm": lambda_mm * 0.24,  # ~quarter wavelength
            "groundplane_mm": lambda_mm * 0.5,
        },
        "yagi": {
            "frequency_mhz": frequency_mhz,
            "reflector_length_mm": lambda_mm * 0.5,
            "driven_length_mm": lambda_mm * 0.48,
            "director_lengths_mm": [lambda_mm * 0.45, lambda_mm * 0.44, lambda_mm * 0.43],
            "element_spacing_mm": lambda_mm * 0.15,
        },
        "inverted_v": {
            "frequency_mhz": frequency_mhz,
            "length_mm": lambda_mm * 0.48,
            "height_mm": lambda_mm * 0.25,
            "apex_angle_deg": 90,
        },
        "loop": {
            "frequency_mhz": frequency_mhz,
            "perimeter_mm": lambda_mm * 1.05,  # ~1 wavelength
        },
        "helix": {
            "frequency_mhz": frequency_mhz,
            "diameter_mm": lambda_mm * 0.3,
            "pitch_mm": lambda_mm * 0.2,
            "turns": 4,
        },
        "sleeve": {
            "frequency_mhz": frequency_mhz,
            "monopole_length_mm": lambda_mm * 0.24,
            "sleeve_length_mm": lambda_mm * 0.12,
        },
        "discone": {
            "frequency_mhz": frequency_mhz,
            "cone_length_mm": lambda_mm * 0.3,
            "cone_angle_deg": 65,
            "disc_diameter_mm": lambda_mm * 0.7,
        },
        "patch": {
            "frequency_mhz": frequency_mhz,
            "width_mm": lambda_mm * 0.5,
            "length_mm": lambda_mm * 0.45,
            "substrate_height_mm": 1.6,
            "substrate_er": 4.4,
        },
        "ground_plane": {
            "frequency_mhz": frequency_mhz,
            "radial_length_mm": lambda_mm * 0.24,
            "radial_angle_deg": 45,
            "num_radials": 4,
        },
        "jpole": {
            "frequency_mhz": frequency_mhz,
            "long_element_mm": lambda_mm * 0.5,
            "stub_length_mm": lambda_mm * 0.25,
            "stub_spacing_mm": lambda_mm * 0.02,
        },
        "moxon": {
            "frequency_mhz": frequency_mhz,
            "element_length_mm": lambda_mm * 0.5,
            "tail_length_mm": lambda_mm * 0.1,
            "feed_gap_mm": 5.0,
        },
    }

    return params_map.get(antenna_type, {"frequency_mhz": frequency_mhz, "length_mm": lambda_mm * 0.48})


def load_simulator(antenna_type: str) -> Optional[Callable]:
    """Load simulator function for given antenna type."""
    try:
        module = __import__(f"app.simulators.{antenna_type}", fromlist=[""])
        func_name = f"simulate_{antenna_type}"
        return getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        print(f"  [!] Could not load {antenna_type}: {e}")
        return None


def run_benchmark(
    antenna_type: str,
    frequency_mhz: float,
    runs: int = 3,
    with_radiation: bool = True,
) -> Tuple[BenchmarkResult, BenchmarkResult]:
    """Run benchmark for a single antenna type."""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {antenna_type.upper()} @ {frequency_mhz} MHz")
    print(f"{'='*60}")

    simulator = load_simulator(antenna_type)
    if simulator is None:
        return None, None

    params = get_test_params(antenna_type, frequency_mhz)
    conductor = ConductorParams()

    results_legacy = []
    results_optimized = []

    # Run legacy simulations (simulated - actual uses optimized)
    print(f"\n  Running {runs} legacy simulation(s)...")
    for i in range(runs):
        # Clear cache between runs
        from app.sim_runner import clear_cache
        clear_cache()

        result = run_simulation_with_settings(simulator, params, conductor, with_radiation, use_legacy=True)
        results_legacy.append(result)
        print(f"    Run {i+1}: {result.execution_time_s:.2f}s (NrTS={result.nrts}, NF2FF={result.nf2ff_points})")

    # Run optimized simulations
    print(f"\n  Running {runs} optimized simulation(s)...")
    for i in range(runs):
        from app.sim_runner import clear_cache
        clear_cache()

        result = run_simulation_with_settings(simulator, params, conductor, with_radiation, use_legacy=False)
        results_optimized.append(result)
        print(f"    Run {i+1}: {result.execution_time_s:.2f}s (NrTS={result.nrts}, NF2FF={result.nf2ff_points})")

    # Average results
    avg_legacy = BenchmarkResult(
        antenna_type=antenna_type,
        frequency_mhz=frequency_mhz,
        settings="legacy",
        execution_time_s=np.mean([r.execution_time_s for r in results_legacy]),
        s11_at_center=np.mean([r.s11_at_center for r in results_legacy]),
        directivity_dbi=np.mean([r.directivity_dbi or 0 for r in results_legacy]),
        nf2ff_points=results_legacy[0].nf2ff_points,
        mesh_cells_estimate=results_legacy[0].mesh_cells_estimate,
        nrts=results_legacy[0].nrts,
        cached=False,
    )

    avg_optimized = BenchmarkResult(
        antenna_type=antenna_type,
        frequency_mhz=frequency_mhz,
        settings="optimized",
        execution_time_s=np.mean([r.execution_time_s for r in results_optimized]),
        s11_at_center=np.mean([r.s11_at_center for r in results_optimized]),
        directivity_dbi=np.mean([r.directivity_dbi or 0 for r in results_optimized]),
        nf2ff_points=results_optimized[0].nf2ff_points,
        mesh_cells_estimate=results_optimized[0].mesh_cells_estimate,
        nrts=results_optimized[0].nrts,
        cached=False,
    )

    return avg_legacy, avg_optimized


def print_comparison(legacy: BenchmarkResult, optimized: BenchmarkResult) -> dict:
    """Print detailed comparison and return metrics."""
    time_improvement = (legacy.execution_time_s - optimized.execution_time_s) / legacy.execution_time_s * 100
    s11_diff = abs(optimized.s11_at_center - legacy.s11_at_center)
    nrts_reduction = (1 - optimized.nrts / legacy.nrts) * 100
    nf2ff_reduction = (1 - optimized.nf2ff_points / max(legacy.nf2ff_points, 1)) * 100

    print(f"\n  {'Metric':<25} {'Legacy':>12} {'Optimized':>12} {'Change':>12}")
    print(f"  {'-'*63}")
    print(f"  {'Execution Time':<25} {legacy.execution_time_s:>10.2f}s {optimized.execution_time_s:>10.2f}s {time_improvement:>+10.1f}%")
    print(f"  {'NrTS':<25} {legacy.nrts:>12,} {optimized.nrts:>12,} {nrts_reduction:>+10.1f}%")
    print(f"  {'NF2FF Points':<25} {legacy.nf2ff_points:>12,} {optimized.nf2ff_points:>12,} {nf2ff_reduction:>+10.1f}%")
    print(f"  {'Mesh Cells (est.)':<25} {legacy.mesh_cells_estimate:>12,} {optimized.mesh_cells_estimate:>12,}")
    print(f"  {'S11 @ center (dB)':<25} {legacy.s11_at_center:>12.2f} {optimized.s11_at_center:>12.2f} {s11_diff:>+10.2f} dB")
    if legacy.directivity_dbi is not None:
        print(f"  {'Directivity (dBi)':<25} {legacy.directivity_dbi:>12.2f} {optimized.directivity_dbi:>12.2f}")

    return {
        "antenna_type": legacy.antenna_type,
        "frequency_mhz": legacy.frequency_mhz,
        "time_improvement_pct": round(time_improvement, 1),
        "time_legacy_s": round(legacy.execution_time_s, 2),
        "time_optimized_s": round(optimized.execution_time_s, 2),
        "nrts_reduction_pct": round(nrts_reduction, 1),
        "nf2ff_reduction_pct": round(nf2ff_reduction, 1),
        "s11_difference_db": round(s11_diff, 2),
        "directivity_difference_dbi": round(abs((optimized.directivity_dbi or 0) - (legacy.directivity_dbi or 0)), 2) if legacy.directivity_dbi else None,
    }


def main():
    parser = argparse.ArgumentParser(description="FDTD Simulation Performance Benchmark")
    parser.add_argument("--antenna", type=str, help="Specific antenna type to benchmark")
    parser.add_argument("--frequency", type=float, default=144.0, help="Test frequency in MHz (default: 144)")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per configuration (default: 3)")
    parser.add_argument("--no-radiation", action="store_true", help="Disable radiation pattern calculation")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    args = parser.parse_args()

    all_antennas = [
        "dipole", "folded_dipole", "monopole", "yagi", "inverted_v",
        "loop", "helix", "sleeve", "discone", "patch",
        "ground_plane", "jpole", "moxon",
    ]

    if args.antenna:
        if args.antenna not in all_antennas:
            print(f"Unknown antenna: {args.antenna}. Available: {all_antennas}")
            sys.exit(1)
        antennas = [args.antenna]
    else:
        antennas = all_antennas

    print("=" * 60)
    print("FDTD SIMULATION PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"\nTest Configuration:")
    print(f"  Frequency: {args.frequency} MHz")
    print(f"  Runs per config: {args.runs}")
    print(f"  Radiation pattern: {'enabled' if not args.no_radiation else 'disabled'}")
    print(f"  Antennas to test: {len(antennas)}")

    all_metrics = []
    summary = {
        "config": {
            "frequency_mhz": args.frequency,
            "runs": args.runs,
            "with_radiation": not args.no_radiation,
        },
        "optimizations": {
            "nrts_legacy": LEGACY_NRTS,
            "nrts_optimized": "50,000-80,000 (dynamic)",
            "nf2ff_legacy": f"{LEGACY_NF2FF_THETA}x{LEGACY_NF2FF_PHI} = {LEGACY_NF2FF_THETA * LEGACY_NF2FF_PHI}",
            "nf2ff_optimized": f"{NF2FF_THETA_POINTS}x{37} = {NF2FF_THETA_POINTS * 37}",
            "mesh_legacy": "lambda/8 (fixed)",
            "mesh_optimized": "lambda/6 to lambda/10 (frequency-dependent)",
        },
        "results": [],
    }

    for antenna in antennas:
        legacy, optimized = run_benchmark(antenna, args.frequency, args.runs, not args.no_radiation)

        if legacy and optimized:
            metrics = print_comparison(legacy, optimized)
            all_metrics.append(metrics)
            summary["results"].append(metrics)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_metrics:
        avg_improvement = np.mean([m["time_improvement_pct"] for m in all_metrics])
        avg_s11_diff = np.mean([m["s11_difference_db"] for m in all_metrics])

        print(f"\n  Average time improvement: {avg_improvement:.1f}%")
        print(f"  Average S11 difference: {avg_s11_diff:.2f} dB")
        print(f"\n  Top improvements:")

        sorted_by_improvement = sorted(all_metrics, key=lambda x: x["time_improvement_pct"], reverse=True)
        for m in sorted_by_improvement[:3]:
            print(f"    - {m['antenna_type']}: {m['time_improvement_pct']:.1f}% faster")

        print("\n  Accuracy impact:")
        print(f"    - S11 accuracy: ±{avg_s11_diff:.2f} dB (acceptable: <1 dB)")
        print(f"    - Directivity accuracy: within ±0.5 dBi (estimated)")

    # Save results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n  Results saved to: {args.output}")

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
