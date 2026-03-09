# backend/app/simulators/loop.py
"""
Loop antenna simulator with aggressively optimized FDTD parameters.

Optimizations applied:
- Coarse mesh resolution (λ/6.0) - loop is electrically large, smooth currents
- Reduced NrTS (50,000 base) - loop converges quickly
- Aggressive NF2FF sampling (13x20 = 260 points vs 37x73 = 2701)
- Skip XML export when not needed

Performance targets:
- Standard loop: <2s
- ΔS11: <0.5 dB vs legacy
"""
import os
import shutil
import tempfile
import math

import numpy as np

from app.conductor import ConductorParams
from app.models import LoopParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_loop(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = LoopParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6

    # Optimized: Coarse mesh for loop (electrically large, smooth current distribution)
    # Loop perimeter is typically ~1λ, currents vary smoothly → λ/6.0 sufficient
    res = get_dynamic_mesh_resolution(f0, lambda_divisor=6.0)

    # Optimized: Reduced NrTS - loop converges quickly (simple closed structure)
    nrts = get_optimized_nrts(f0, "loop", with_radiation)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap = 2.0

    side = p.perimeter_mm / 4.0  # side length for square loop

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)
    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    half = side / 2.0
    mesh.AddLine("x", [-half - pad, -half, 0, half, half + pad])
    mesh.AddLine("y", [-pad, 0, pad])
    mesh.AddLine("z", [-half - pad, -half, -gap / 2, gap / 2, half, half + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("loop")
    # Bottom side (with feed gap)
    metal.AddCylinder([-half, 0, -half], [half, 0, -half], radius)  # bottom
    metal.AddCylinder([half, 0, -half], [half, 0, half], radius)  # right
    metal.AddCylinder([-half, 0, half], [half, 0, half], radius)  # top
    # Left side with feed gap at z=0
    metal.AddCylinder([-half, 0, -half], [-half, 0, -gap / 2], radius)
    metal.AddCylinder([-half, 0, gap / 2], [-half, 0, half], radius)

    port = FDTD.AddLumpedPort(1, 50, [-half, 0, -gap / 2], [-half, 0, gap / 2], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_loop_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "loop.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "loop",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        
        if with_radiation and nf2ff is not None:
            # Optimized: Aggressive NF2FF sampling for loop
            # Loop has simple bidirectional pattern (broadside/edge)
            # 13x20 = 260 points, 90% faster than legacy 37x73 = 2701 points
            theta, phi = get_nf2ff_sampling(with_radiation, high_resolution=False, antenna_type="loop")
            nf2ff_res = nf2ff.CalcNF2FF(sim_dir, [f0], theta, phi)
            e_abs = np.abs(nf2ff_res.E_norm[0])
            e_max = float(e_abs.max())
            if e_max > 0:
                e_db = 20.0 * np.log10(e_abs / e_max + 1e-12)
            else:
                e_db = np.zeros_like(e_abs)
            result["results"]["radiation"] = {
                "theta_deg": np.degrees(theta).tolist(),
                "phi_deg": np.degrees(phi).tolist(),
                "e_norm_db": e_db.tolist(),
                "directivity_dbi": float(np.max(nf2ff_res.Dmax)),
                "frequency_mhz": float(f0 / 1e6),
                "nf2ff_points": len(theta) * len(phi),
            }
        
        return result
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
