# backend/app/simulators/patch.py
"""
Patch antenna simulator with optimized FDTD parameters.

Optimizations applied:
- Dynamic mesh resolution based on frequency
- Reduced NrTS (80,000 vs 300,000)
- Optimized NF2FF sampling (19x37 vs 37x73)
- Skip XML export when not needed
"""
import os
import shutil
import tempfile

import numpy as np

from app.conductor import ConductorParams
from app.models import PatchParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_patch(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = PatchParams(**params)

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6

    # Optimized: Dynamic mesh resolution based on frequency
    res = get_dynamic_mesh_resolution(f0)
    
    # Optimized: Reduced NrTS with EndCriteria (patch is complex)
    nrts = get_optimized_nrts(f0, "patch", with_radiation)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap = 2.0

    w = p.width_mm
    l = p.length_mm
    h = p.substrate_height_mm
    er = p.substrate_er

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)
    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-w / 2 - pad, -w / 2, 0, w / 2, w / 2 + pad])
    mesh.AddLine("y", [-l / 2 - pad, -l / 2, 0, l / 2, l / 2 + pad])
    mesh.AddLine("z", [-pad, 0, h, h + gap])
    mesh.SmoothMeshLines("all", res, 1.4)

    # Dielectric substrate
    sub = CSX.AddMaterial("substrate", epsilon=er)
    sub.AddBox([-w / 2 - pad, -l / 2 - pad, 0], [w / 2 + pad, l / 2 + pad, h])

    # Ground plane
    gp = CSX.AddMetal("groundplane")
    gp.AddBox([-w / 2 - pad, -l / 2 - pad, 0], [w / 2 + pad, l / 2 + pad, 0])

    # Patch
    patch = CSX.AddMetal("patch")
    patch.AddBox([-w / 2, -l / 2, h], [w / 2, l / 2, h])

    # Feed port through substrate at edge (y = -l/2, center of width)
    port = FDTD.AddLumpedPort(1, 50, [0, -l / 2, 0], [0, -l / 2, h], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_patch_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "patch.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "patch",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        
        if with_radiation and nf2ff is not None:
            # Optimized: Reduced NF2FF sampling points
            theta, phi = get_nf2ff_sampling(with_radiation, high_resolution=False)
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
