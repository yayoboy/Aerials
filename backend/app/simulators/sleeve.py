# backend/app/simulators/sleeve.py
"""
Sleeve monopole antenna simulator with aggressively optimized FDTD parameters.

Optimizations applied:
- Coarse mesh resolution (λ/6.5) - sleeve structure is simple coaxial
- Reduced NrTS (50,000 base) - sleeve converges quickly
- Aggressive NF2FF sampling (13x25 = 325 points vs 37x73 = 2701)
- Skip XML export when not needed

Performance targets:
- Standard sleeve: <5s
- ΔS11: <0.5 dB vs legacy
"""
import os
import shutil
import tempfile

import numpy as np

from app.conductor import ConductorParams
from app.models import SleeveParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_sleeve(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = SleeveParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6

    # Optimized: Coarse mesh for sleeve (simple coaxial structure)
    # Sleeve has cylindrical symmetry, λ/6.5 is sufficient
    res = get_dynamic_mesh_resolution(f0, lambda_divisor=6.5)

    # Optimized: Reduced NrTS - sleeve converges quickly (simple structure)
    nrts = get_optimized_nrts(f0, "sleeve", with_radiation)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap = 2.0
    sleeve_r = radius * 4  # sleeve outer radius, 4x wire radius

    total_h = p.monopole_length_mm + gap

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)
    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-sleeve_r - pad, -sleeve_r, 0, sleeve_r, sleeve_r + pad])
    mesh.AddLine("y", [-sleeve_r - pad, -sleeve_r, 0, sleeve_r, sleeve_r + pad])
    mesh.AddLine("z", [-pad, 0, gap, p.sleeve_length_mm, total_h, total_h + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    # Sleeve (coaxial outer conductor, bottom half)
    sleeve = CSX.AddMetal("sleeve")
    sleeve.AddCylinder([0, 0, 0], [0, 0, p.sleeve_length_mm], sleeve_r)

    # Monopole (inner conductor, full length above gap)
    mono = CSX.AddMetal("monopole")
    mono.AddCylinder([0, 0, gap], [0, 0, total_h], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_sleeve_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "sleeve.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "sleeve",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        
        if with_radiation and nf2ff is not None:
            # Optimized: Aggressive NF2FF sampling for sleeve
            # Sleeve has omnidirectional pattern (monopole-like)
            # 13x25 = 325 points, 88% faster than legacy 37x73 = 2701 points
            theta, phi = get_nf2ff_sampling(with_radiation, high_resolution=False, antenna_type="sleeve")
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
