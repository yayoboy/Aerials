import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import MonopoleParams

def simulate_monopole(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = MonopoleParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0        = p.frequency_mhz * 1e6
    length    = p.length_mm
    gp_radius = p.groundplane_mm / 2.0
    c0        = 299792458.0
    lambda0   = c0 / f0 * 1000.0
    res       = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad       = lambda0 / 4.0
    gap       = 2.0

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-gp_radius - pad, -gp_radius, 0, gp_radius, gp_radius + pad])
    mesh.AddLine('y', [-gp_radius - pad, -gp_radius, 0, gp_radius, gp_radius + pad])
    mesh.AddLine('z', [-pad, 0, gap, length, length + pad])
    mesh.SmoothMeshLines('all', res)

    gp = CSX.AddMetal('groundplane')
    gp.AddBox([-gp_radius, -gp_radius, 0], [gp_radius, gp_radius, 0])

    mono = CSX.AddMetal('monopole')
    mono.AddCylinder([0, 0, gap], [0, 0, length], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_mono_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'mono.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "monopole", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(),
                            "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
