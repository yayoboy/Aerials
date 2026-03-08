# backend/app/simulators/dipole.py
import os, sys, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import DipoleParams

def simulate_dipole(params: dict, conductor: ConductorParams = None, with_radiation: bool = False) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = DipoleParams(**params)

    try:
        import CSXCAD, openEMS
    except ImportError as e:
        raise

    f0     = p.frequency_mhz * 1e6
    length = p.length_mm
    radius = conductor.effective_radius_mm()

    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    f_max   = f0 * 1.5
    lambda_min = c0 / f_max * 1000.0
    res     = lambda_min / 10.0

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    pad = lambda0 / 4.0
    gap = 2.0

    mesh.AddLine('x', [-pad - radius, 0, pad + radius])
    mesh.AddLine('y', [-pad - radius, 0, pad + radius])
    mesh.AddLine('z', [-length/2 - pad, -length/2, -gap/2, gap/2, length/2, length/2 + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('dipole')
    metal.AddCylinder([0, 0,  gap/2], [0, 0,  length/2], radius)
    metal.AddCylinder([0, 0, -gap/2], [0, 0, -length/2], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, -gap/2], [0, 0, gap/2], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_dipole_")
    try:
        if with_radiation:
            nf2ff = FDTD.CreateNF2FFBox()
        CSX.Write2XML(os.path.join(sim_dir, 'dipole.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        result = {
            "antenna_type": "dipole",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
        if with_radiation:
            theta = np.linspace(0, np.pi, 37)
            phi   = np.linspace(0, 2 * np.pi, 73)
            nf2ff.CalcNF2FF(sim_dir, [f0], theta, phi)
            e_abs = np.abs(nf2ff.E_norm[0])
            e_max = float(e_abs.max())
            if e_max > 0:
                e_db = 20.0 * np.log10(e_abs / e_max + 1e-12)
            else:
                e_db = np.zeros_like(e_abs)
            result["results"]["radiation"] = {
                "theta_deg":       np.degrees(theta).tolist(),
                "phi_deg":         np.degrees(phi).tolist(),
                "e_norm_db":       e_db.tolist(),
                "directivity_dbi": float(np.max(nf2ff.Dmax)),
                "frequency_mhz":   float(f0 / 1e6),
            }
        return result
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
