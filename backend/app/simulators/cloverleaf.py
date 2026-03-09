# backend/app/simulators/cloverleaf.py
"""
Cloverleaf (3-blade) antenna simulator.

Three circular loops arranged at 120° azimuthal spacing, each tilted at
`tilt_deg` from vertical.  All loops share a common feed point at the
origin — the classic design used for circular-polarisation video links
in FPV multirotor racing (typically 5.8 GHz).
"""
import os
import shutil
import tempfile
import math

import numpy as np

from app.conductor import ConductorParams
from app.models import CloverleafParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)

_SEGS_PER_LOOP = 14   # polygon approximation segments per loop


def _loop_points(loop_r: float, phi_k: float, tilt_deg: float, n: int, z_offset: float):
    """
    Return n+1 points for loop k.

    The loop lies in the plane spanned by the radial direction (phi_k) and Z.
    It passes through (0, 0, z_offset) at t=0 (the feed/junction point).
    """
    tilt = math.radians(tilt_deg)
    cp, sp = math.cos(phi_k), math.sin(phi_k)
    st, ct = math.sin(tilt), math.cos(tilt)

    # Centre of the loop (distance = loop_r from the junction point)
    cx = loop_r * st * cp
    cy = loop_r * st * sp
    cz = loop_r * ct + z_offset

    # e_a: from centre back to junction (normalised)
    e_ax, e_ay, e_az = -st * cp, -st * sp, -ct
    # e_b: perpendicular to e_a within the blade plane
    e_bx, e_by, e_bz = ct * cp, ct * sp, -st

    pts = []
    for i in range(n + 1):
        t = 2.0 * math.pi * i / n
        co, si = math.cos(t), math.sin(t)
        pts.append((
            cx + loop_r * (co * e_ax + si * e_bx),
            cy + loop_r * (co * e_ay + si * e_by),
            cz + loop_r * (co * e_az + si * e_bz),
        ))
    return pts


def simulate_cloverleaf(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = CloverleafParams(**params)

    import CSXCAD, openEMS

    f0       = p.frequency_mhz * 1e6
    loop_r   = p.loop_diameter_mm / 2.0
    tilt_deg = p.tilt_deg
    radius   = conductor.effective_radius_mm()
    gap      = max(2.0, loop_r * 0.06)   # feed gap scales with loop size

    res  = get_dynamic_mesh_resolution(f0, lambda_divisor=8.0)
    nrts = get_optimized_nrts(f0, "cloverleaf", with_radiation)
    pad  = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)

    bbox = loop_r * 2.2   # approximate extent

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-bbox - pad, -bbox, 0, bbox, bbox + pad])
    mesh.AddLine("y", [-bbox - pad, -bbox, 0, bbox, bbox + pad])
    mesh.AddLine("z", [-pad, 0, gap / 2, loop_r * 2, loop_r * 2 + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("cloverleaf")

    # Build 3 loops; all start/end at z = gap/2 (the junction above the port)
    for k in range(3):
        phi_k = 2.0 * math.pi * k / 3.0
        pts   = _loop_points(loop_r, phi_k, tilt_deg, _SEGS_PER_LOOP, gap / 2)
        for i in range(len(pts) - 1):
            metal.AddCylinder(list(pts[i]), list(pts[i + 1]), radius)

    # Feed port at base of the junction (z = 0 → z = gap/2)
    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap / 2], "z", 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_cloverleaf_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()

        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "cloverleaf.xml"))

        FDTD.Run(sim_dir, verbose=0)

        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))

        result = {
            "antenna_type": "cloverleaf",
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
