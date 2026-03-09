# backend/app/simulators/vivaldi.py
"""
Vivaldi (Tapered Slot Antenna, TSA) simulator.

Two flat metal half-sheets separated by an exponentially tapered slot.
The narrow feed end (slot_width) expands to the full aperture
(aperture_width) over the antenna length — giving ultra-wideband,
end-fire radiation.  Modelled as a step-tapered approximation.
"""
import os
import shutil
import tempfile
import math

import numpy as np

from app.conductor import ConductorParams
from app.models import VivaldiParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)

_N_STEPS = 10    # taper approximation steps


def simulate_vivaldi(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = VivaldiParams(**params)

    import CSXCAD, openEMS

    f0       = p.frequency_mhz * 1e6
    length   = p.length_mm
    ap_w     = p.aperture_width_mm
    slot_w   = p.slot_width_mm
    sheet_w  = ap_w * 1.3            # total sheet width
    t        = max(conductor.effective_radius_mm() * 2, 0.5)  # sheet thickness
    gap      = slot_w                 # port gap = initial slot width

    res  = get_dynamic_mesh_resolution(f0, lambda_divisor=10.0)
    nrts = get_optimized_nrts(f0, "vivaldi", with_radiation)
    pad  = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-sheet_w / 2 - pad, -sheet_w / 2, -slot_w / 2, 0, slot_w / 2, sheet_w / 2, sheet_w / 2 + pad])
    mesh.AddLine("y", [-t / 2 - pad, -t / 2, 0, t / 2, t / 2 + pad])
    mesh.AddLine("z", [-pad, 0, length, length + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    # Exponential taper coefficient
    if ap_w > slot_w:
        alpha = math.log(ap_w / slot_w) / length
    else:
        alpha = 0.0

    metal = CSX.AddMetal("vivaldi")
    for n in range(_N_STEPS):
        z1 = n * length / _N_STEPS
        z2 = (n + 1) * length / _N_STEPS
        # Slot half-width at mid-step (exponential taper)
        z_mid  = (z1 + z2) / 2.0
        sw_half = (slot_w / 2.0) * math.exp(alpha * z_mid)

        # Left half-sheet
        metal.AddBox(
            [-sheet_w / 2, -t / 2, z1],
            [-sw_half,      t / 2, z2],
        )
        # Right half-sheet
        metal.AddBox(
            [sw_half,       -t / 2, z1],
            [sheet_w / 2,   t / 2, z2],
        )

    # Feed port across the slot at the narrow (z=0) end
    port = FDTD.AddLumpedPort(
        1, 50,
        [-slot_w / 2, 0, 0], [slot_w / 2, 0, 0],
        "x", 1.0,
    )

    sim_dir = tempfile.mkdtemp(prefix="openems_vivaldi_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()

        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "vivaldi.xml"))

        FDTD.Run(sim_dir, verbose=0)

        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))

        result = {
            "antenna_type": "vivaldi",
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
