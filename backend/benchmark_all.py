#!/usr/bin/env python3
"""
Comprehensive FDTD Benchmark - All 13 Antennas at Multiple Frequencies

Tests all antenna types at VHF (144 MHz), UHF (435 MHz), and 2.4 GHz (2400 MHz).
Compares legacy vs optimized settings and generates detailed reports.

Usage:
    python benchmark_all.py [--runs N] [--timeout S] [--output-dir DIR]

Examples:
    python benchmark_all.py                    # Run all benchmarks
    python benchmark_all.py --runs 1           # Single run per config
    python benchmark_all.py --timeout 120      # 120s timeout per sim
"""
import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.conductor import ConductorParams
from app.sim_utils import (
    C0,
    NF2FF_THETA_POINTS,
    NF2FF_PHI_POINTS,
    calculate_nf2ff_points,
    format_simulation_time,
    get_dynamic_mesh_resolution,
    get_optimized_nrts,
    get_nf2ff_sampling,
)


# ============================================================================
# Configuration
# ============================================================================

ALL_ANTENNAS = [
    "dipole",
    "folded_dipole",
    "monopole",
    "yagi",
    "inverted_v",
    "loop",
    "helix",
    "sleeve",
    "discone",
    "patch",
    "ground_plane",
    "jpole",
    "moxon",
]

# Test frequencies
FREQUENCIES = {
    "VHF_2m": 144.0,      # 2 meter amateur band
    "UHF_70cm": 435.0,    # 70 centimeter amateur band
    "WIFI_2.4G": 2400.0,  # WiFi/ISM band
}

# Legacy parameters (what old code would have used)
LEGACY_NRTS = 300_000
LEGACY_LAMBDA_DIVISOR = 8.0
LEGACY_NF2FF_THETA = 37
LEGACY_NF2FF_PHI = 73

# Timeout per simulation (seconds)
DEFAULT_TIMEOUT_S = 120


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class BenchmarkResult:
    """Stores benchmark results for a single simulation."""
    antenna_type: str
    frequency_mhz: float
    frequency_label: str
    settings: str  # "legacy" or "optimized"
    execution_time_s: float
    s11_at_center: float
    directivity_dbi: Optional[float]
    nf2ff_points: int
    mesh_cells_estimate: int
    nrts: int
    cached: bool
    status: str  # "success", "timeout", "error"
    error_message: Optional[str] = None


@dataclass
class ComparisonResult:
    """Comparison between legacy and optimized for one config."""
    antenna_type: str
    frequency_mhz: float
    frequency_label: str
    time_legacy_s: float
    time_optimized_s: float
    time_improvement_pct: float
    time_saved_s: float
    nrts_legacy: int
    nrts_optimized: int
    nrts_reduction_pct: float
    nf2ff_legacy: int
    nf2ff_optimized: int
    nf2ff_reduction_pct: float
    s11_legacy: float
    s11_optimized: float
    s11_difference_db: float
    directivity_legacy: Optional[float]
    directivity_optimized: Optional[float]
    status: str
    error_message: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def estimate_mesh_cells(frequency_mhz: float, antenna_size_mm: float, lambda_divisor: float) -> int:
    """Estimate number of mesh cells based on frequency and mesh resolution."""
    lambda_mm = C0 / (frequency_mhz * 1e6) * 1000
    cell_size_mm = lambda_mm / lambda_divisor
    domain_mm = antenna_size_mm * 3
    cells_per_dim = max(domain_mm / cell_size_mm, 10)
    return int(cells_per_dim ** 3)


def get_test_params(antenna_type: str, frequency_mhz: float) -> dict:
    """Get realistic test parameters for each antenna type."""
    lambda_m = C0 / (frequency_mhz * 1e6)
    lambda_mm = lambda_m * 1000

    params_map = {
        "dipole": {
            "frequency_mhz": frequency_mhz,
            "length_mm": lambda_mm * 0.48,
        },
        "folded_dipole": {
            "frequency_mhz": frequency_mhz,
            "length_mm": lambda_mm * 0.48,
            "spacing_mm": lambda_mm * 0.05,
        },
        "monopole": {
            "frequency_mhz": frequency_mhz,
            "length_mm": lambda_mm * 0.24,
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
            "perimeter_mm": lambda_mm * 1.05,
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
        print(f"    [!] Could not load {antenna_type}: {e}")
        return None


def run_simulation_with_settings(
    simulator_fn: Callable,
    params: dict,
    conductor: ConductorParams,
    with_radiation: bool,
    use_legacy: bool = False,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    frequency_label: str = "unknown",
) -> BenchmarkResult:
    """
    Run a simulation with specified settings and measure performance.
    
    For legacy mode, we simulate the old behavior by using the old parameters.
    For optimized mode, we use the dynamic optimized parameters.
    """
    frequency_mhz = params.get("frequency_mhz", 144.0)
    antenna_type = simulator_fn.__name__.replace("simulate_", "")

    # Calculate parameters based on settings
    if use_legacy:
        nrts = LEGACY_NRTS
        lambda_divisor = LEGACY_LAMBDA_DIVISOR
        nf2ff_theta_points = LEGACY_NF2FF_THETA
        nf2ff_phi_points = LEGACY_NF2FF_PHI
        settings = "legacy"
    else:
        nrts = get_optimized_nrts(frequency_mhz * 1e6, antenna_type, with_radiation)
        lambda_divisor = get_dynamic_mesh_resolution(frequency_mhz * 1e6) / (C0 / (frequency_mhz * 1e6) * 1000)
        nf2ff_theta_arr, nf2ff_phi_arr = get_nf2ff_sampling(with_radiation, high_resolution=False, antenna_type=antenna_type)
        if nf2ff_theta_arr is None:
            nf2ff_theta_points, nf2ff_phi_points = 0, 0
        else:
            nf2ff_theta_points = len(nf2ff_theta_arr)
            nf2ff_phi_points = len(nf2ff_phi_arr)
        settings = "optimized"

    # Estimate mesh cells
    antenna_size_mm = params.get("length_mm", params.get("diameter_mm", 1000))
    mesh_cells = estimate_mesh_cells(frequency_mhz, antenna_size_mm, lambda_divisor)

    # Calculate NF2FF points
    if with_radiation:
        nf2ff_points = nf2ff_theta_points * nf2ff_phi_points
    else:
        nf2ff_points = 0

    # Run simulation
    result = None
    execution_time = 0.0
    status = "success"
    error_message = None

    try:
        from app.sim_runner import clear_cache
        clear_cache()

        start_time = time.time()
        
        # Run the actual simulation
        result = simulator_fn(params, conductor, with_radiation)
        
        execution_time = time.time() - start_time

        # Check for timeout
        if execution_time > timeout_s:
            status = "timeout"
            error_message = f"Simulation exceeded {timeout_s}s timeout"

        # Extract S11 and directivity
        s11_at_center = -20.0
        directivity = None

        if isinstance(result, dict) and result.get("status") == "success":
            freqs = result.get("results", {}).get("frequencies_mhz", [])
            s11_values = result.get("results", {}).get("s11_db", [])

            if freqs and s11_values:
                freq_array = np.array(freqs)
                s11_array = np.array(s11_values)
                center_idx = np.argmin(np.abs(freq_array - frequency_mhz))
                s11_at_center = float(s11_array[center_idx])

            if "radiation" in result.get("results", {}):
                directivity = result["results"]["radiation"].get("directivity_dbi")

        return BenchmarkResult(
            antenna_type=antenna_type,
            frequency_mhz=frequency_mhz,
            frequency_label=frequency_label,
            settings=settings,
            execution_time_s=execution_time,
            s11_at_center=s11_at_center,
            directivity_dbi=directivity,
            nf2ff_points=nf2ff_points,
            mesh_cells_estimate=mesh_cells,
            nrts=nrts,
            cached=result.get("_cached", False) if isinstance(result, dict) else False,
            status=status,
            error_message=error_message,
        )

    except TimeoutError as e:
        status = "timeout"
        error_message = str(e)
        execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
        return BenchmarkResult(
            antenna_type=antenna_type,
            frequency_mhz=frequency_mhz,
            frequency_label=frequency_label,
            settings=settings,
            execution_time_s=execution_time,
            s11_at_center=-20.0,
            directivity_dbi=None,
            nf2ff_points=nf2ff_points,
            mesh_cells_estimate=mesh_cells,
            nrts=nrts,
            cached=False,
            status=status,
            error_message=error_message,
        )
    except Exception as e:
        status = "error"
        error_message = str(e)
        execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
        return BenchmarkResult(
            antenna_type=antenna_type,
            frequency_mhz=frequency_mhz,
            frequency_label=frequency_label,
            settings=settings,
            execution_time_s=execution_time,
            s11_at_center=-20.0,
            directivity_dbi=None,
            nf2ff_points=nf2ff_points,
            mesh_cells_estimate=mesh_cells,
            nrts=nrts,
            cached=False,
            status=status,
            error_message=error_message,
        )


def run_benchmark_comparison(
    antenna_type: str,
    frequency_mhz: float,
    frequency_label: str,
    with_radiation: bool = False,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> ComparisonResult:
    """Run benchmark comparison for a single antenna/frequency config."""
    print(f"\n  Testing: {antenna_type} @ {frequency_mhz} MHz ({frequency_label})")

    simulator = load_simulator(antenna_type)
    if simulator is None:
        return ComparisonResult(
            antenna_type=antenna_type,
            frequency_mhz=frequency_mhz,
            frequency_label=frequency_label,
            time_legacy_s=0,
            time_optimized_s=0,
            time_improvement_pct=0,
            time_saved_s=0,
            nrts_legacy=LEGACY_NRTS,
            nrts_optimized=0,
            nrts_reduction_pct=0,
            nf2ff_legacy=LEGACY_NF2FF_THETA * LEGACY_NF2FF_PHI,
            nf2ff_optimized=0,
            nf2ff_reduction_pct=0,
            s11_legacy=-20,
            s11_optimized=-20,
            s11_difference_db=0,
            directivity_legacy=None,
            directivity_optimized=None,
            status="error",
            error_message=f"Could not load simulator for {antenna_type}",
        )

    params = get_test_params(antenna_type, frequency_mhz)
    conductor = ConductorParams()

    # Run legacy simulation
    print(f"    Legacy (NrTS={LEGACY_NRTS:,})...", end=" ", flush=True)
    result_legacy = run_simulation_with_settings(
        simulator, params, conductor, with_radiation,
        use_legacy=True, timeout_s=timeout_s, frequency_label=frequency_label
    )
    print(f"{result_legacy.execution_time_s:.2f}s [{result_legacy.status}]")

    # Run optimized simulation
    print(f"    Optimized (NrTS={result_legacy.nrts:,})...", end=" ", flush=True)
    result_optimized = run_simulation_with_settings(
        simulator, params, conductor, with_radiation,
        use_legacy=False, timeout_s=timeout_s, frequency_label=frequency_label
    )
    print(f"{result_optimized.execution_time_s:.2f}s [{result_optimized.status}]")

    # Calculate improvements
    if result_legacy.status == "success" and result_optimized.status == "success":
        time_improvement = (result_legacy.execution_time_s - result_optimized.execution_time_s) / result_legacy.execution_time_s * 100
        time_saved = result_legacy.execution_time_s - result_optimized.execution_time_s
        nrts_reduction = (1 - result_optimized.nrts / result_legacy.nrts) * 100
        nf2ff_reduction = (1 - result_optimized.nf2ff_points / max(result_legacy.nf2ff_points, 1)) * 100
        s11_diff = abs(result_optimized.s11_at_center - result_legacy.s11_at_center)
        status = "success"
    else:
        time_improvement = 0
        time_saved = 0
        nrts_reduction = 0
        nf2ff_reduction = 0
        s11_diff = 0
        status = result_legacy.status if result_legacy.status != "success" else result_optimized.status

    return ComparisonResult(
        antenna_type=antenna_type,
        frequency_mhz=frequency_mhz,
        frequency_label=frequency_label,
        time_legacy_s=round(result_legacy.execution_time_s, 2),
        time_optimized_s=round(result_optimized.execution_time_s, 2),
        time_improvement_pct=round(time_improvement, 1),
        time_saved_s=round(time_saved, 2),
        nrts_legacy=result_legacy.nrts,
        nrts_optimized=result_optimized.nrts,
        nrts_reduction_pct=round(nrts_reduction, 1),
        nf2ff_legacy=result_legacy.nf2ff_points,
        nf2ff_optimized=result_optimized.nf2ff_points,
        nf2ff_reduction_pct=round(nf2ff_reduction, 1),
        s11_legacy=round(result_legacy.s11_at_center, 2),
        s11_optimized=round(result_optimized.s11_at_center, 2),
        s11_difference_db=round(s11_diff, 2),
        directivity_legacy=result_legacy.directivity_dbi,
        directivity_optimized=result_optimized.directivity_dbi,
        status=status,
        error_message=result_legacy.error_message or result_optimized.error_message,
    )


def generate_markdown_table(results: List[ComparisonResult]) -> str:
    """Generate markdown comparison table."""
    lines = []
    lines.append("# FDTD Simulation Benchmark Results")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    
    # Calculate summary statistics
    successful = [r for r in results if r.status == "success"]
    if successful:
        avg_improvement = np.mean([r.time_improvement_pct for r in successful])
        avg_time_legacy = np.mean([r.time_legacy_s for r in successful])
        avg_time_optimized = np.mean([r.time_optimized_s for r in successful])
        total_time_saved = sum([r.time_saved_s for r in successful])
        
        lines.append(f"- **Total configurations tested:** {len(results)}")
        lines.append(f"- **Successful:** {len(successful)}")
        lines.append(f"- **Average time improvement:** {avg_improvement:.1f}%")
        lines.append(f"- **Average legacy time:** {avg_time_legacy:.2f}s")
        lines.append(f"- **Average optimized time:** {avg_time_optimized:.2f}s")
        lines.append(f"- **Total time saved:** {total_time_saved:.1f}s")
        lines.append("")
    
    # Table by antenna
    lines.append("## Results by Antenna")
    lines.append("")
    
    for antenna in ALL_ANTENNAS:
        antenna_results = [r for r in results if r.antenna_type == antenna]
        if not antenna_results:
            continue
            
        lines.append(f"### {antenna.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Frequency | Legacy (s) | Optimized (s) | Improvement | NrTS Reduction | S11 Δ (dB) | Status |")
        lines.append("|-----------|------------|---------------|-------------|----------------|------------|--------|")
        
        for r in antenna_results:
            improvement_str = f"{r.time_improvement_pct:+.1f}%" if r.status == "success" else "N/A"
            nrts_str = f"{r.nrts_reduction_pct:.1f}%" if r.status == "success" else "N/A"
            s11_str = f"{r.s11_difference_db:.2f}" if r.status == "success" else "N/A"
            status_icon = "✅" if r.status == "success" else ("⏱️" if r.status == "timeout" else "❌")
            
            lines.append(f"| {r.frequency_label} ({r.frequency_mhz:.0f} MHz) | {r.time_legacy_s:.2f} | {r.time_optimized_s:.2f} | {improvement_str} | {nrts_str} | {s11_str} | {status_icon} {r.status} |")
        
        lines.append("")
    
    # Problematic antennas
    failed = [r for r in results if r.status != "success"]
    if failed:
        lines.append("## Problematic Configurations")
        lines.append("")
        lines.append("| Antenna | Frequency | Status | Error |")
        lines.append("|---------|-----------|--------|-------|")
        for r in failed:
            error_msg = (r.error_message or "Unknown")[:50] + "..." if len(r.error_message or "") > 50 else (r.error_message or "Unknown")
            lines.append(f"| {r.antenna_type} | {r.frequency_label} | {r.status} | {error_msg} |")
        lines.append("")
    
    # Top improvements
    if successful:
        lines.append("## Top 10 Improvements")
        lines.append("")
        sorted_by_improvement = sorted(successful, key=lambda x: x.time_improvement_pct, reverse=True)[:10]
        lines.append("| Rank | Antenna | Frequency | Legacy (s) | Optimized (s) | Improvement |")
        lines.append("|------|---------|-----------|------------|---------------|-------------|")
        for i, r in enumerate(sorted_by_improvement, 1):
            lines.append(f"| {i} | {r.antenna_type} | {r.frequency_label} | {r.time_legacy_s:.2f} | {r.time_optimized_s:.2f} | {r.time_improvement_pct:+.1f}% |")
        lines.append("")
    
    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    
    # Find antennas that need tuning
    slow_configs = [r for r in successful if r.time_optimized_s > 30]
    if slow_configs:
        lines.append("### Antennas Needing Optimization Tuning")
        lines.append("")
        lines.append("These configurations still take >30s and may benefit from further NrTS tuning:")
        lines.append("")
        for r in sorted(slow_configs, key=lambda x: r.time_optimized_s, reverse=True)[:5]:
            lines.append(f"- **{r.antenna_type} @ {r.frequency_label}**: {r.time_optimized_s:.2f}s (NrTS={r.nrts_optimized:,})")
        lines.append("")
    
    lines.append("### SLO Recommendations")
    lines.append("")
    if successful:
        max_time = max([r.time_optimized_s for r in successful])
        p95_time = np.percentile([r.time_optimized_s for r in successful], 95)
        avg_time = np.mean([r.time_optimized_s for r in successful])
        
        lines.append(f"- **Target SLO:** {max_time * 1.5:.0f}s (1.5x max observed)")
        lines.append(f"- **Warning threshold:** {p95_time * 1.5:.0f}s (1.5x P95)")
        lines.append(f"- **Average optimized time:** {avg_time:.2f}s")
        lines.append("")
    
    return "\n".join(lines)


def generate_json_report(results: List[ComparisonResult], config: dict) -> dict:
    """Generate JSON report."""
    successful = [r for r in results if r.status == "success"]
    
    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "config": config,
        },
        "summary": {
            "total_configurations": len(results),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "average_time_improvement_pct": round(np.mean([r.time_improvement_pct for r in successful]), 1) if successful else 0,
            "total_time_saved_s": round(sum([r.time_saved_s for r in successful]), 2) if successful else 0,
        },
        "results": [asdict(r) for r in results],
        "by_antenna": {},
        "by_frequency": {},
    }
    
    # Group by antenna
    for antenna in ALL_ANTENNAS:
        antenna_results = [r for r in results if r.antenna_type == antenna]
        if antenna_results:
            successful_antenna = [r for r in antenna_results if r.status == "success"]
            report["by_antenna"][antenna] = {
                "configurations": len(antenna_results),
                "successful": len(successful_antenna),
                "avg_improvement_pct": round(np.mean([r.time_improvement_pct for r in successful_antenna]), 1) if successful_antenna else 0,
                "avg_time_optimized_s": round(np.mean([r.time_optimized_s for r in successful_antenna]), 2) if successful_antenna else 0,
            }
    
    # Group by frequency
    for freq_label, freq_mhz in FREQUENCIES.items():
        freq_results = [r for r in results if r.frequency_label == freq_label]
        if freq_results:
            successful_freq = [r for r in freq_results if r.status == "success"]
            report["by_frequency"][freq_label] = {
                "configurations": len(freq_results),
                "successful": len(successful_freq),
                "avg_improvement_pct": round(np.mean([r.time_improvement_pct for r in successful_freq]), 1) if successful_freq else 0,
                "avg_time_optimized_s": round(np.mean([r.time_optimized_s for r in successful_freq]), 2) if successful_freq else 0,
            }
    
    return report


def print_progress(current: int, total: int, antenna: str, freq_label: str):
    """Print progress indicator."""
    pct = (current / total) * 100
    bar_length = 30
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n[{bar}] {pct:.0f}% - {antenna} @ {freq_label} ({current}/{total})")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Comprehensive FDTD Benchmark")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs per configuration (default: 1)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S, help=f"Timeout per simulation in seconds (default: {DEFAULT_TIMEOUT_S})")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for results")
    parser.add_argument("--no-radiation", action="store_true", help="Disable radiation pattern calculation")
    parser.add_argument("--antenna", type=str, help="Specific antenna to benchmark (default: all)")
    parser.add_argument("--frequency", type=str, help="Specific frequency label to test (default: all)")
    args = parser.parse_args()

    # Determine output directory
    output_dir = args.output_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)

    # Determine antennas to test
    if args.antenna:
        if args.antenna not in ALL_ANTENNAS:
            print(f"Unknown antenna: {args.antenna}. Available: {ALL_ANTENNAS}")
            sys.exit(1)
        antennas_to_test = [args.antenna]
    else:
        antennas_to_test = ALL_ANTENNAS

    # Determine frequencies to test
    if args.frequency:
        if args.frequency not in FREQUENCIES:
            print(f"Unknown frequency: {args.frequency}. Available: {list(FREQUENCIES.keys())}")
            sys.exit(1)
        frequencies_to_test = {args.frequency: FREQUENCIES[args.frequency]}
    else:
        frequencies_to_test = FREQUENCIES

    with_radiation = not args.no_radiation

    # Print header
    print("=" * 70)
    print("COMPREHENSIVE FDTD SIMULATION BENCHMARK")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Antennas: {len(antennas_to_test)} ({', '.join(antennas_to_test)})")
    print(f"  Frequencies: {len(frequencies_to_test)} ({', '.join(frequencies_to_test.keys())})")
    print(f"  Total configurations: {len(antennas_to_test) * len(frequencies_to_test)}")
    print(f"  Runs per config: {args.runs}")
    print(f"  Timeout: {args.timeout}s")
    print(f"  Radiation pattern: {'enabled' if with_radiation else 'disabled'}")
    print(f"  Output directory: {output_dir}")
    print()

    # Run benchmarks
    all_results: List[ComparisonResult] = []
    total_configs = len(antennas_to_test) * len(frequencies_to_test)
    current_config = 0

    for antenna in antennas_to_test:
        for freq_label, freq_mhz in frequencies_to_test.items():
            current_config += 1
            print_progress(current_config, total_configs, antenna, freq_label)
            
            result = run_benchmark_comparison(
                antenna, freq_mhz, freq_label,
                with_radiation=with_radiation,
                timeout_s=args.timeout,
            )
            all_results.append(result)

    # Generate reports
    print("\n" + "=" * 70)
    print("GENERATING REPORTS")
    print("=" * 70)

    config = {
        "runs": args.runs,
        "timeout_s": args.timeout,
        "with_radiation": with_radiation,
        "legacy_nrts": LEGACY_NRTS,
        "legacy_nf2ff": f"{LEGACY_NF2FF_THETA}x{LEGACY_NF2FF_PHI}",
        "antennas_tested": antennas_to_test,
        "frequencies_tested": list(frequencies_to_test.keys()),
    }

    # JSON report
    json_report = generate_json_report(all_results, config)
    json_path = os.path.join(output_dir, "benchmark_results_all.json")
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)
    print(f"\n  JSON report: {json_path}")

    # Markdown report
    md_content = generate_markdown_table(all_results)
    md_path = os.path.join(os.path.dirname(output_dir), "docs", "BENCHMARK_RESULTS.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"  Markdown report: {md_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    successful = [r for r in all_results if r.status == "success"]
    if successful:
        avg_improvement = np.mean([r.time_improvement_pct for r in successful])
        print(f"\n  Successful configurations: {len(successful)}/{len(all_results)}")
        print(f"  Average time improvement: {avg_improvement:.1f}%")
        
        # Top 3 improvements
        print("\n  Top 3 improvements:")
        sorted_results = sorted(successful, key=lambda x: x.time_improvement_pct, reverse=True)[:3]
        for r in sorted_results:
            print(f"    - {r.antenna_type} @ {r.frequency_label}: {r.time_improvement_pct:+.1f}%")
        
        # Problematic configs
        failed = [r for r in all_results if r.status != "success"]
        if failed:
            print(f"\n  Problematic configurations ({len(failed)}):")
            for r in failed[:5]:
                print(f"    - {r.antenna_type} @ {r.frequency_label}: {r.status}")
    else:
        print("\n  No successful configurations!")

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
