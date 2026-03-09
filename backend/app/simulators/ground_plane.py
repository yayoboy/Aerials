# backend/app/simulators/ground_plane.py
"""
Ground plane antenna simulator with optimized FDTD parameters.

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
from app.models import GroundPlaneParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_ground_plane(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = GroundPlaneParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6

    # Optimized: Dynamic mesh resolution with VHF-specific lambda_divisor
    res = get_dynamic_mesh_resolution(f0, lambda_divisor=7.0)

    # Optimized: Reduced NrTS with EndCriteria
    nrts = get_optimized_nrts(f0, "ground_plane", with_radiation)

    pad = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap = 2.0

    radial_len = p.radial_length_mm
    angle_rad = math.radians(p.radial_angle_deg)
    radial_x_end = radial_len * math.cos(angle_rad)
    radial_z_end = -radial_len * math.sin(angle_rad)  # downward from feed
    mono_len = radial_len  # monopole same length as radials

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)
    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    # Optimized: Use reduced radials for mesh (3) while keeping simulation radials (4)
    mesh_radials = 3  # Reduced for mesh coarsening
    mesh.AddLine("x", [-radial_x_end - pad, -radial_x_end, 0, radial_x_end, radial_x_end + pad])
    mesh.AddLine("y", [-radial_x_end - pad, -radial_x_end, 0, radial_x_end, radial_x_end + pad])
    mesh.AddLine("z", [radial_z_end - pad, radial_z_end, 0, gap, mono_len + gap, mono_len + gap + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("ground_plane")
    # Monopole element
    metal.AddCylinder([0, 0, gap], [0, 0, mono_len + gap], radius)
    # Radials: equally spaced around the feed point (use full num_radials for simulation)
    for i in range(p.num_radials):
        theta = 2 * math.pi * i / p.num_radials
        end_x = radial_x_end * math.cos(theta)
        end_y = radial_x_end * math.sin(theta)
        metal.AddCylinder([0, 0, 0], [end_x, end_y, radial_z_end], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_gp_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        
        # Optimized: Skip XML export if environment variable is set
        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "gp.xml"))
        
        FDTD.Run(sim_dir, verbose=0)
        
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11 = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        
        result = {
            "antenna_type": "ground_plane",
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
