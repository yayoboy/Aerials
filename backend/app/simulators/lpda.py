# backend/app/simulators/lpda.py
"""
Log-Periodic Dipole Array (LPDA) antenna simulator.

Element lengths and spacings are scaled geometrically by the factor tau.
The centre element is tuned to λ/2 at the design frequency; elements
longer than λ/2 act as reflectors, shorter ones as directors.

This simplified model drives the centre element directly and treats all
others as parasitic — the result gives a good approximation of gain,
S11 and radiation pattern across the log-periodic bandwidth.
"""
import os
import shutil
import tempfile

import numpy as np

from app.conductor import ConductorParams
from app.models import LPDAParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)


def simulate_lpda(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = LPDAParams(**params)

    import CSXCAD, openEMS

    f0     = p.frequency_mhz * 1e6
    tau    = p.tau
    sigma  = p.sigma
    n_el   = p.num_elements
    radius = conductor.effective_radius_mm()
    gap    = 2.0

    # Centre element is λ/2 at design frequency
    n_center = n_el // 2
    L_center = C0 / (2.0 * f0) * 1000.0          # mm

    # All element half-lengths (longest first)
    half_lengths = [L_center / 2.0 * (tau ** (i - n_center)) for i in range(n_el)]
    half_lengths.sort(reverse=True)               # index 0 = longest

    # Z positions (boom direction, longest at z=0)
    z_pos = [0.0]
    for i in range(n_el - 1):
        spacing = 2.0 * sigma * half_lengths[i]   # = sigma * full_length_i
        z_pos.append(z_pos[-1] + spacing)

    max_half  = half_lengths[0]
    z_front   = z_pos[-1]   # shortest element position (driven)
    driven_idx = n_el - 1   # we drive the shortest element (high-freq end)

    res  = get_dynamic_mesh_resolution(f0, lambda_divisor=8.0)
    nrts = get_optimized_nrts(f0, "lpda", with_radiation)
    if n_el > 6:
        nrts = int(nrts * 1.2)
    pad  = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-max_half - pad, -max_half, 0, max_half, max_half + pad])
    mesh.AddLine("y", [-pad, 0, pad])

    z_lines = [-pad]
    for z in z_pos:
        z_lines += [z - gap / 2, z, z + gap / 2]
    z_lines.append(z_front + pad)
    mesh.AddLine("z", sorted(set(z_lines)))
    mesh.SmoothMeshLines("all", res, 1.4)

    metal = CSX.AddMetal("lpda")

    # Add all elements; leave gap at driven element for the feed port
    for i, (hl, z) in enumerate(zip(half_lengths, z_pos)):
        if i == driven_idx:
            # Driven element — leave feed gap
            metal.AddCylinder([-hl, 0, z], [-gap / 2, 0, z], radius)
            metal.AddCylinder([ gap / 2, 0, z], [ hl, 0, z], radius)
        else:
            metal.AddCylinder([-hl, 0, z], [hl, 0, z], radius)

    z_d = z_pos[driven_idx]
    port = FDTD.AddLumpedPort(
        1, 50,
        [-gap / 2, 0, z_d], [gap / 2, 0, z_d],
        "x", 1.0,
    )

    sim_dir = tempfile.mkdtemp(prefix="openems_lpda_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()

        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "lpda.xml"))

        FDTD.Run(sim_dir, verbose=0)

        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))

        result = {
            "antenna_type": "lpda",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            },
        }

        if with_radiation and nf2ff is not None:
            theta, phi = get_nf2ff_sampling(
                with_radiation, high_resolution=False, antenna_type="yagi"
            )
            nf2ff_res = nf2ff.CalcNF2FF(sim_dir, [f0], theta, phi)
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
