# backend/app/simulators/inverted_v.py
"""
Inverted-V antenna simulator with aggressively optimized FDTD parameters.

Optimizations applied:
- Apex-angle adaptive mesh: λ/7.0 for wide angles (≥90°), λ/8.0 for narrow
- Reduced NrTS (50,000 base) - inverted V converges quickly
- Aggressive NF2FF sampling (13x20 = 260 points vs 37x73 = 2701)
- Skip XML export when not needed

Performance targets:
- Standard inverted V: <2s
- ΔS11: <0.5 dB vs legacy
"""
import os
import shutil
import tempfile
import math

import numpy as np

from app.conductor import ConductorParams
from app.models import InvertedVParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_inverted_v(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = InvertedVParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6

    # Optimized: Apex-angle adaptive mesh resolution
    # Wide apex angles (≥90°) have smoother current distribution → coarser mesh OK
    # Narrow angles (<90°) need finer mesh for accuracy at apex
    lambda_div = 7.0 if p.apex_angle_deg >= 90 else 8.0
    res = get_dynamic_mesh_resolution(f0, lambda_divisor=lambda_div)

    # Optimized: Reduced NrTS - inverted V converges quickly (simple wire structure)
    nrts = get_optimized_nrts(f0, "inverted_v", with_radiation)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap = 2.0

    arm_len = p.length_mm / 2.0
    half_angle_rad = math.radians(p.apex_angle_deg / 2.0)
    arm_x = arm_len * math.sin(half_angle_rad)
    arm_z = arm_len * math.cos(half_angle_rad)
    apex_h = p.height_mm

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)
    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-arm_x - pad, -arm_x, 0, arm_x, arm_x + pad])
    mesh.AddLine("y", [-pad, 0, pad])
    mesh.AddLine("z", [-pad, 0, apex_h - arm_z, apex_h - gap / 2, apex_h + gap / 2, apex_h + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("inverted_v")
    # Left arm: from apex down-left
    metal.AddCylinder([0, 0, apex_h - gap / 2], [-arm_x, 0, apex_h - arm_z], radius)
    # Right arm: from apex down-right
    metal.AddCylinder([0, 0, apex_h + gap / 2], [arm_x, 0, apex_h - arm_z], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, apex_h - gap / 2], [0, 0, apex_h + gap / 2], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_invertedv_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "iv.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "inverted_v",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        
        if with_radiation and nf2ff is not None:
            # Optimized: Aggressive NF2FF sampling for inverted V
            # Inverted V has simple dipole-like pattern with elevation tilt
            # 13x20 = 260 points, 90% faster than legacy 37x73 = 2701 points
            theta, phi = get_nf2ff_sampling(with_radiation, high_resolution=False, antenna_type="inverted_v")
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
