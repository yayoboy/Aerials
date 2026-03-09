# backend/app/simulators/biconical.py
"""
Biconical antenna simulator.

Two identical cones with their apices touching at the feed gap.
The wideband, symmetrical geometry gives an impedance close to 50-200 Ω
over more than a decade of frequency, making it popular for
EMC measurements and UHF broadband links.
"""
import os
import shutil
import tempfile
import math

import numpy as np

from app.conductor import ConductorParams
from app.models import BiconicalParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_biconical(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = BiconicalParams(**params)

    import CSXCAD, openEMS

    f0     = p.frequency_mhz * 1e6
    cl     = p.cone_length_mm
    ang    = math.radians(p.cone_angle_deg)     # half-angle from axis
    cr     = cl * math.sin(ang)                 # base radius of each cone
    radius = conductor.effective_radius_mm()
    gap    = 2.0
    n_wires = 8   # radial wires per cone

    res  = get_dynamic_mesh_resolution(f0, lambda_divisor=6.5)
    nrts = get_optimized_nrts(f0, "biconical", with_radiation)
    pad  = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-cr - pad, -cr, 0, cr, cr + pad])
    mesh.AddLine("y", [-cr - pad, -cr, 0, cr, cr + pad])
    mesh.AddLine("z", [-cl - pad, -cl, -gap / 2, gap / 2, cl, cl + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    cone = CSX.AddMetal("biconical")
    for k in range(n_wires):
        theta = 2.0 * math.pi * k / n_wires
        bx = cr * math.cos(theta)
        by = cr * math.sin(theta)
        # Upper cone: apex at +gap/2, base at +cl
        cone.AddCylinder([0, 0,  gap / 2], [bx, by,  cl], radius)
        # Lower cone: apex at -gap/2, base at -cl
        cone.AddCylinder([0, 0, -gap / 2], [bx, by, -cl], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, -gap / 2], [0, 0, gap / 2], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_biconical_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()

        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "biconical.xml"))

        FDTD.Run(sim_dir, verbose=0)

        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))

        result = {
            "antenna_type": "biconical",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            },
        }

        if with_radiation and nf2ff is not None:
            theta_samp, phi_samp = get_nf2ff_sampling(
                with_radiation, high_resolution=False
            )
            nf2ff_res = nf2ff.CalcNF2FF(sim_dir, [f0], theta_samp, phi_samp)
            e_abs = np.abs(nf2ff_res.E_norm[0])
            e_max = float(e_abs.max())
            e_db  = 20.0 * np.log10(e_abs / e_max + 1e-12) if e_max > 0 else np.zeros_like(e_abs)
            result["results"]["radiation"] = {
                "theta_deg":      np.degrees(theta_samp).tolist(),
                "phi_deg":        np.degrees(phi_samp).tolist(),
                "e_norm_db":      e_db.tolist(),
                "directivity_dbi": float(np.max(nf2ff_res.Dmax)),
                "frequency_mhz":  float(f0 / 1e6),
                "nf2ff_points":   len(theta_samp) * len(phi_samp),
            }

        return result
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
