# backend/app/simulators/rhombic.py
"""
Rhombic (diamond) antenna simulator.

Four equal wire legs form a flat rhombus in the XZ plane.
A lumped feed sits at the front apex; a resistive termination (600 Ω)
at the rear apex suppresses backward radiation and flattens the pattern.
The acute apex angle determines tilt of the main lobe.
"""
import os
import shutil
import tempfile
import math

import numpy as np

from app.conductor import ConductorParams
from app.models import RhombicParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)

_RHOMBIC_TERM_OHM = 600.0   # typical rhombic termination resistance


def simulate_rhombic(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = RhombicParams(**params)

    import CSXCAD, openEMS

    f0     = p.frequency_mhz * 1e6
    leg    = p.leg_length_mm
    half_a = math.radians(p.apex_angle_deg / 2.0)
    radius = conductor.effective_radius_mm()
    gap    = 2.0

    # Rhombus vertices in XZ plane
    x_side = leg * math.sin(half_a)
    z_mid  = leg * math.cos(half_a)
    z_rear = 2.0 * z_mid

    res  = get_dynamic_mesh_resolution(f0)
    nrts = get_optimized_nrts(f0, "rhombic", with_radiation)
    pad  = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-x_side - pad, -x_side, 0, x_side, x_side + pad])
    mesh.AddLine("y", [-pad, 0, pad])
    mesh.AddLine("z", [-pad, 0, gap / 2, z_mid, z_rear - gap / 2, z_rear, z_rear + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    wire = CSX.AddMetal("rhombic")
    # Front apex → side vertices (leaving gap at z=0 for feed)
    wire.AddCylinder([0, 0, gap / 2], [-x_side, 0, z_mid], radius)
    wire.AddCylinder([0, 0, gap / 2], [ x_side, 0, z_mid], radius)
    # Side vertices → rear apex (leaving gap at z_rear for termination)
    wire.AddCylinder([-x_side, 0, z_mid], [0, 0, z_rear - gap / 2], radius)
    wire.AddCylinder([ x_side, 0, z_mid], [0, 0, z_rear - gap / 2], radius)

    # Feed port (front apex, along Z)
    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap / 2], "z", 1.0)

    # Termination resistor (rear apex, not driven)
    FDTD.AddLumpedPort(
        2, _RHOMBIC_TERM_OHM,
        [0, 0, z_rear - gap / 2], [0, 0, z_rear],
        "z", 0.0,
    )

    sim_dir = tempfile.mkdtemp(prefix="openems_rhombic_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()

        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "rhombic.xml"))

        FDTD.Run(sim_dir, verbose=0)

        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))

        result = {
            "antenna_type": "rhombic",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            },
        }

        if with_radiation and nf2ff is not None:
            theta, phi = get_nf2ff_sampling(with_radiation, high_resolution=False)
            nf2ff_res  = nf2ff.CalcNF2FF(sim_dir, [f0], theta, phi)
            e_abs = np.abs(nf2ff_res.E_norm[0])
            e_max = float(e_abs.max())
            e_db  = 20.0 * np.log10(e_abs / e_max + 1e-12) if e_max > 0 else np.zeros_like(e_abs)
            result["results"]["radiation"] = {
                "theta_deg":      np.degrees(theta).tolist(),
                "phi_deg":        np.degrees(phi).tolist(),
                "e_norm_db":      e_db.tolist(),
                "directivity_dbi": float(np.max(nf2ff_res.Dmax)),
                "frequency_mhz":  float(f0 / 1e6),
                "nf2ff_points":   len(theta) * len(phi),
            }

        return result
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
