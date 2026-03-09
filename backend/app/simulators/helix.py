# backend/app/simulators/helix.py
"""
Helix antenna simulator with optimized FDTD parameters.

Optimizations applied:
- Dynamic mesh resolution based on frequency
- Reduced NrTS (80,000 vs 300,000)
- Optimized NF2FF sampling (19x37 vs 37x73)
- Skip XML export when not needed
"""
import os
import shutil
import tempfile
import math

import numpy as np

from app.conductor import ConductorParams
from app.models import HelixParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_helix(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = HelixParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6

    # Optimized: Dynamic mesh resolution based on frequency with helix-specific lambda_divisor
    res = get_dynamic_mesh_resolution(f0, lambda_divisor=5.5)

    # Optimized: Reduced NrTS with EndCriteria (helix is complex)
    nrts = get_optimized_nrts(f0, "helix", with_radiation)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap = 2.0

    helix_r = p.diameter_mm / 2.0
    total_h = p.turns * p.pitch_mm
    steps_per_turn = 12  # Optimized: reduced from 16 to 12 for helix structure
    total_steps = p.turns * steps_per_turn

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)
    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-helix_r - pad, -helix_r, 0, helix_r, helix_r + pad])
    mesh.AddLine("y", [-helix_r - pad, -helix_r, 0, helix_r, helix_r + pad])
    mesh.AddLine("z", [-pad, gap, total_h, total_h + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("helix")
    # Ground plane
    gp = CSX.AddMetal("gp")
    gp.AddBox([-helix_r - pad / 2, -helix_r - pad / 2, 0], [helix_r + pad / 2, helix_r + pad / 2, 0])

    # Helix winding
    for i in range(total_steps):
        theta1 = 2 * math.pi * i / steps_per_turn
        theta2 = 2 * math.pi * (i + 1) / steps_per_turn
        z1 = gap + (i / total_steps) * total_h
        z2 = gap + ((i + 1) / total_steps) * total_h
        p1 = [helix_r * math.cos(theta1), helix_r * math.sin(theta1), z1]
        p2 = [helix_r * math.cos(theta2), helix_r * math.sin(theta2), z2]
        metal.AddCylinder(p1, p2, radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_helix_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "helix.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "helix",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        
        if with_radiation and nf2ff is not None:
            # Optimized: Reduced NF2FF sampling points (13x25=325 vs 19x37=703)
            theta_samples = 13
            phi_samples = 25
            theta = np.linspace(0, np.pi, theta_samples)
            phi = np.linspace(0, 2 * np.pi, phi_samples)
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
