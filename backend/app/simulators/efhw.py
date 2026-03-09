# backend/app/simulators/efhw.py
"""
End-Fed Half-Wave (EFHW) antenna simulator.

A half-wave wire fed at one end.  The feed-point impedance is very high
(~2450 Ω) and requires an external 49:1 UNUN transformer to match 50 Ω
coax.  A small counterpoise (λ/20) provides the RF return path.

The S11 shown here is normalised to 2450 Ω so resonance appears as a
deep null — confirming the wire is tuned to half a wavelength.
"""
import os
import shutil
import tempfile

import numpy as np

from app.conductor import ConductorParams
from app.models import EFHWParams
from app.sim_utils import (
    C0,
    get_dynamic_mesh_resolution,
    get_nf2ff_sampling,
    get_optimized_nrts,
    skip_xml_export,
)

_EFHW_IMPEDANCE = 2450.0   # Ω  (typical end-fed λ/2 impedance)


def simulate_efhw(
    params: dict,
    conductor: ConductorParams = None,
    with_radiation: bool = False,
) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = EFHWParams(**params)

    import CSXCAD, openEMS

    f0     = p.frequency_mhz * 1e6
    length = p.length_mm
    cp_len = p.counterpoise_mm     # short counterpoise / RF-return stub
    radius = conductor.effective_radius_mm()
    gap    = 2.0

    res  = get_dynamic_mesh_resolution(f0)
    nrts = get_optimized_nrts(f0, "efhw", with_radiation)
    pad  = (0.6 if with_radiation else 0.2) * (C0 / f0 * 1000.0)

    FDTD = openEMS.openEMS(EndCriteria=1e-3, NrTS=nrts)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(["PML_4" if with_radiation else "PML_8"] * 6)

    CSX = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine("x", [-cp_len - pad, -cp_len, 0, cp_len, cp_len + pad])
    mesh.AddLine("y", [-pad - radius, 0, pad + radius])
    mesh.AddLine("z", [-pad, 0, gap, length, length + pad])
    mesh.SmoothMeshLines("all", res, 1.4)

    # Main half-wave wire (upward from feed gap)
    wire = CSX.AddMetal("efhw_wire")
    wire.AddCylinder([0, 0, gap], [0, 0, length], radius)

    # Counterpoise: two short radials in ±X to model the RF-return stub
    cp = CSX.AddMetal("counterpoise")
    cp.AddCylinder([0, 0, 0], [ cp_len, 0, 0], radius)
    cp.AddCylinder([0, 0, 0], [-cp_len, 0, 0], radius)

    # High-impedance lumped port — S11 ≈ 0 dB when impedance matches 2450 Ω
    port = FDTD.AddLumpedPort(
        1, _EFHW_IMPEDANCE, [0, 0, 0], [0, 0, gap], "z", 1.0
    )

    sim_dir = tempfile.mkdtemp(prefix="openems_efhw_")
    try:
        nf2ff = None
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()

        if not skip_xml_export():
            CSX.Write2XML(os.path.join(sim_dir, "efhw.xml"))

        FDTD.Run(sim_dir, verbose=0)

        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))

        result = {
            "antenna_type": "efhw",
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
