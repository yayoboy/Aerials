# backend/app/sim_utils.py
"""
Shared utilities for FDTD simulation optimization.

Provides:
- Dynamic mesh resolution based on frequency
- Optimized NrTS calculation
- Reduced NF2FF sampling points
- Common simulation setup patterns
"""
import numpy as np
from typing import Tuple, Optional


# Speed of light in m/s
C0 = 299_792_458.0

# Optimized FDTD parameters
DEFAULT_NRTS = 80_000  # Reduced from 300,000
DEFAULT_END_CRITERIA = 1e-3

# NF2FF optimized sampling (75% faster than 37x73)
NF2FF_THETA_POINTS = 19  # Reduced from 37
NF2FF_PHI_POINTS = 37    # Reduced from 37-73

# Aggressive NF2FF sampling for fast simulations (85%+ faster)
# For antennas with simple/symmetric radiation patterns
NF2FF_THETA_POINTS_FAST = 13
NF2FF_PHI_POINTS_FAST = 20

# Yagi-specific NF2FF (directional pattern, fewer phi points needed)
NF2FF_THETA_POINTS_YAGI = 15
NF2FF_PHI_POINTS_YAGI = 20

# Sleeve-specific NF2FF (omnidirectional, moderate sampling)
NF2FF_THETA_POINTS_SLEEVE = 13
NF2FF_PHI_POINTS_SLEEVE = 25

# Original high-resolution sampling (for accuracy-critical simulations)
NF2FF_THETA_POINTS_HR = 37
NF2FF_PHI_POINTS_HR = 73


def get_dynamic_mesh_resolution(
    frequency_hz: float,
    lambda_divisor: Optional[float] = None,
) -> float:
    """
    Calculate optimal mesh resolution based on operating frequency.
    
    Higher frequencies need finer mesh. Lower frequencies can use coarser mesh.
    
    Args:
        frequency_hz: Operating frequency in Hz
        lambda_divisor: Optional override for lambda/X ratio
    
    Returns:
        Mesh resolution in mm (same units as wavelength calculation)
    
    Rules:
        - f < 100 MHz:   lambda/6  (coarser, faster)
        - 100-500 MHz:   lambda/8  (standard)
        - f > 500 MHz:   lambda/10 (finer, more accurate)
    """
    if lambda_divisor is not None:
        # Use provided divisor
        lambda_m = C0 / frequency_hz
        return (lambda_m / lambda_divisor) * 1000.0  # Convert to mm
    
    frequency_mhz = frequency_hz / 1e6
    
    if frequency_mhz < 100:
        divisor = 6.0
    elif frequency_mhz <= 500:
        divisor = 8.0
    else:
        divisor = 10.0
    
    lambda_m = C0 / frequency_hz
    return (lambda_m / divisor) * 1000.0  # Convert to mm


def get_optimized_nrts(
    frequency_hz: float,
    antenna_type: str = "default",
    with_radiation: bool = False,
) -> int:
    """
    Calculate optimal number of time steps based on antenna type and frequency.
    
    Args:
        frequency_hz: Operating frequency in Hz
        antenna_type: Type of antenna (affects convergence time)
        with_radiation: Whether radiation pattern is being calculated
    
    Returns:
        Number of time steps (NrTS)
    
    Rules:
        - Simple antennas (dipole, monopole): 50,000 steps
        - Complex antennas (yagi, helix, patch): 80,000 steps
        - With radiation: +20% steps for NF2FF convergence
    """
    # Base steps by antenna complexity
    simple_antennas = {"dipole", "folded_dipole", "monopole", "inverted_v", "loop", "jpole", "moxon"}
    # Helix-specific: complex 3D geometry but converges faster than discone/yagi
    # Benchmark shows 20s+ at VHF; reducing from 80k to 60k targets <10s
    helix_specific = {"helix"}

    if antenna_type in simple_antennas:
        base_steps = 50_000
    elif antenna_type in helix_specific:
        base_steps = 60_000
    else:
        base_steps = 80_000
    
    # Increase for radiation calculations
    if with_radiation:
        base_steps = int(base_steps * 1.2)
    
    # Ensure minimum and cap
    return max(30_000, min(base_steps, 150_000))


def get_nf2ff_sampling(
    with_radiation: bool,
    high_resolution: bool = False,
    antenna_type: str = "default",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get optimized theta/phi sampling for NF2FF calculations.

    Args:
        with_radiation: Whether to return sampling arrays
        high_resolution: Use high-resolution sampling (slower but more accurate)
        antenna_type: Type of antenna for antenna-specific sampling patterns

    Returns:
        Tuple of (theta_array, phi_array) in radians
        If with_radiation=False, returns (None, None)
    """
    if not with_radiation:
        return None, None

    if high_resolution:
        theta_points = NF2FF_THETA_POINTS_HR
        phi_points = NF2FF_PHI_POINTS_HR
    else:
        # Antenna-specific sampling for aggressive optimization
        if antenna_type == "yagi":
            theta_points = NF2FF_THETA_POINTS_YAGI
            phi_points = NF2FF_PHI_POINTS_YAGI
        elif antenna_type == "sleeve":
            theta_points = NF2FF_THETA_POINTS_SLEEVE
            phi_points = NF2FF_PHI_POINTS_SLEEVE
        elif antenna_type in ("loop", "inverted_v"):
            theta_points = NF2FF_THETA_POINTS_FAST
            phi_points = NF2FF_PHI_POINTS_FAST
        else:
            theta_points = NF2FF_THETA_POINTS
            phi_points = NF2FF_PHI_POINTS

    theta = np.linspace(0, np.pi, theta_points)
    phi = np.linspace(0, 2 * np.pi, phi_points)

    return theta, phi


def calculate_nf2ff_points(theta: np.ndarray, phi: np.ndarray) -> int:
    """Calculate total number of NF2FF sampling points."""
    if theta is None or phi is None:
        return 0
    return len(theta) * len(phi)


def skip_xml_export() -> bool:
    """
    Determine if XML export should be skipped for performance.
    
    Returns True if environment variable SKIP_XML_EXPORT is set.
    """
    import os
    return os.environ.get("SKIP_XML_EXPORT", "false").lower() == "true"


def format_simulation_time(seconds: float) -> str:
    """Format simulation time in human-readable format."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
