# backend/app/simulators/turnstile.py
"""
Turnstile antenna simulator.

Two half-wave dipoles crossed at 90 degrees and driven in-phase.
Produces a near-omnidirectional pattern in the horizontal plane with
elliptical/circular polarisation (quadrature feed requires external splitter).
"""
import os
import shutil
import tempfile

import numpy as np

from app.conductor import ConductorParams
from app.models import TurnstileParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_turnstile(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = TurnstileParams(**params)

    import CSXCAD, openEMS

    f0 = p.frequency_mhz * 1e6
    arm = p.arm_length_mm          # half-length of each dipole (centre to tip)
    radius = conductor.effective_radius_mm()

    res  = get_dynamic_mesh_resolution(f0)
    nrts = get_optimized_nrts(f0, "turnstile", with_radiation)
    pad  = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)
    gap  = 2.0

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-arm - pad, -arm, -gap / 2, gap / 2, arm, arm + pad])
    mesh.AddLine("y", [-arm - pad, -arm, -gap / 2, gap / 2, arm, arm + pad])
    mesh.AddLine("z", [-pad, 0, pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("turnstile")
    # X-axis dipole
    metal.AddCylinder([-arm, 0, 0], [-gap / 2, 0, 0], radius)
    metal.AddCylinder([ gap / 2, 0, 0], [ arm, 0, 0], radius)
    # Y-axis dipole
    metal.AddCylinder([0, -arm, 0], [0, -gap / 2, 0], radius)
    metal.AddCylinder([0,  gap / 2, 0], [0,  arm, 0], radius)

    # Both ports driven in-phase (true circular polarisation needs 90° phase shift
    # via an external hybrid coupler — not modelled here)
    port1 = FDTD.AddLumpedPort(1, 50, [-gap / 2, 0, 0], [gap / 2, 0, 0], "x", 1.0)
    port2 = FDTD.AddLumpedPort(2, 50, [0, -gap / 2, 0], [0,  gap / 2, 0], "y", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_turnstile_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()

        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "turnstile.xml"))

        FDTD.Run(sim_dir, verbose=0)

        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port1.CalcPort(sim_dir, f_eval)
        port2.CalcPort(sim_dir, f_eval)

        # S11 referred to port 1 (X-dipole)
        s11    = port1.uf_ref / port1.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))

        result = {
            "antenna_type": "turnstile",
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
