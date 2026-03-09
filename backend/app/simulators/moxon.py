# backend/app/simulators/moxon.py
"""
Moxon antenna simulator with optimized FDTD parameters.

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
from app.models import MoxonParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_moxon(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = MoxonParams(**params)

    try:
        import CSXCAD, openEMS
    except ImportError as e:
        raise

    f0 = p.frequency_mhz * 1e6
    A = p.element_length_mm  # total width (mm)
    B = p.tail_length_mm  # tail depth (mm)
    C = p.feed_gap_mm  # feed gap (mm)
    radius = conductor.effective_radius_mm()

    # Optimized: Dynamic mesh resolution based on frequency
    res = get_dynamic_mesh_resolution(f0)
    
    # Optimized: Reduced NrTS with EndCriteria
    nrts = get_optimized_nrts(f0, "moxon", with_radiation)

    # Gap between tail tips (Cebik: ~0.5% of wavelength)
    D = max((C0 / f0 * 1000.0) * 0.005, 1.0)
    depth = B + D + B

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)

    mesh.AddLine("x", [-A / 2 - pad, -A / 2, -C / 2, C / 2, A / 2, A / 2 + pad])
    mesh.AddLine("y", [-pad, 0, B, B + D, depth, depth + pad])
    mesh.AddLine("z", [-pad - radius, 0, pad + radius])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("moxon")
    # Driven element halves
    metal.AddCylinder([-A / 2, 0, 0], [-C / 2, 0, 0], radius)
    metal.AddCylinder([C / 2, 0, 0], [A / 2, 0, 0], radius)
    # Driven element tails
    metal.AddCylinder([-A / 2, 0, 0], [-A / 2, B, 0], radius)
    metal.AddCylinder([A / 2, 0, 0], [A / 2, B, 0], radius)
    # Reflector
    metal.AddCylinder([-A / 2, depth, 0], [A / 2, depth, 0], radius)
    # Reflector tails
    metal.AddCylinder([-A / 2, depth - B, 0], [-A / 2, depth, 0], radius)
    metal.AddCylinder([A / 2, depth - B, 0], [A / 2, depth, 0], radius)

    # Feed port between driven element halves
    port = FDTD.AddLumpedPort(1, 50, [-C / 2, 0, 0], [C / 2, 0, 0], "x", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_moxon_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "moxon.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "moxon",
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
