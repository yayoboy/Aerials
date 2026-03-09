# backend/app/simulators/yagi.py
"""
Yagi-Uda antenna simulator with aggressively optimized FDTD parameters.

Optimizations applied:
- Dynamic mesh resolution based on frequency (λ/8 for Yagi sensitivity)
- Director-based NrTS scaling: +30% for complex Yagis (5+ directors)
- Aggressive NF2FF sampling (15x20 = 300 points vs 37x73 = 2701)
- Skip XML export when not needed

Performance targets:
- Simple Yagi (2-3 elements): <5s
- Complex Yagi (5+ directors): <10s
- ΔS11: <0.5 dB vs legacy
"""
import os
import shutil
import tempfile

import numpy as np

from app.conductor import ConductorParams
from app.models import YagiParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_yagi(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = YagiParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6
    spacing = p.element_spacing_mm

    # Optimized: Dynamic mesh resolution based on frequency
    # Yagi is sensitive to mesh accuracy (directional elements), use λ/8
    res = get_dynamic_mesh_resolution(f0, lambda_divisor=8.0)

    # Optimized: Director-based NrTS scaling
    # More directors = longer convergence time
    num_elements = 2 + len(p.director_lengths_mm)  # reflector + driven + directors
    nrts = get_optimized_nrts(f0, "yagi", with_radiation)
    if num_elements > 4:
        # Complex Yagi (5+ elements): +30% time steps for convergence
        nrts = int(nrts * 1.3)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap = 2.0

    z_ref = 0.0
    z_driven = spacing
    n_dir = len(p.director_lengths_mm)
    z_dirs = [z_driven + (i + 1) * spacing for i in range(n_dir)]
    z_max = z_dirs[-1] if z_dirs else z_driven
    max_half = max(p.reflector_length_mm, p.driven_length_mm, *p.director_lengths_mm) / 2.0

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-max_half - pad, -max_half, 0, max_half, max_half + pad])
    mesh.AddLine("y", [-pad, 0, pad])
    mesh.AddLine("z", [z_ref - pad, z_ref, z_driven - gap / 2, z_driven + gap / 2, z_max, z_max + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("yagi")
    # Reflector
    hr = p.reflector_length_mm / 2.0
    metal.AddCylinder([-hr, 0, z_ref], [hr, 0, z_ref], radius)
    # Driven element with gap
    hd = p.driven_length_mm / 2.0
    metal.AddCylinder([-hd, 0, z_driven], [-gap / 2, 0, z_driven], radius)
    metal.AddCylinder([gap / 2, 0, z_driven], [hd, 0, z_driven], radius)
    # Directors
    for i, dl in enumerate(p.director_lengths_mm):
        hdi = dl / 2.0
        metal.AddCylinder([-hdi, 0, z_dirs[i]], [hdi, 0, z_dirs[i]], radius)

    port = FDTD.AddLumpedPort(1, 50, [-gap / 2, 0, z_driven], [gap / 2, 0, z_driven], "x", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_yagi_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "yagi.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "yagi",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        
        if with_radiation and nf2ff is not None:
            # Optimized: Aggressive NF2FF sampling for Yagi
            # Yagi has directional pattern (forward gain), symmetric in phi
            # 15x20 = 300 points vs 300 points (15 theta, 20 phi)
            # 89% faster than legacy 37x73 = 2701 points
            theta, phi = get_nf2ff_sampling(with_radiation, high_resolution=False, antenna_type="yagi")
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
