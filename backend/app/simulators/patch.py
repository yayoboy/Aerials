import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import PatchParams

def simulate_patch(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = PatchParams(**params)

    import CSXCAD, openEMS

    f0     = p.frequency_mhz * 1e6
    c0     = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res    = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad    = lambda0 / 4.0
    gap    = 2.0

    w = p.width_mm
    l = p.length_mm
    h = p.substrate_height_mm
    er = p.substrate_er

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-w/2 - pad, -w/2, 0, w/2, w/2 + pad])
    mesh.AddLine('y', [-l/2 - pad, -l/2, 0, l/2, l/2 + pad])
    mesh.AddLine('z', [-pad, 0, h, h + gap])
    mesh.SmoothMeshLines('all', res)

    # Dielectric substrate
    sub = CSX.AddMaterial('substrate', epsilon=er)
    sub.AddBox([-w/2 - pad, -l/2 - pad, 0], [w/2 + pad, l/2 + pad, h])

    # Ground plane
    gp = CSX.AddMetal('groundplane')
    gp.AddBox([-w/2 - pad, -l/2 - pad, 0], [w/2 + pad, l/2 + pad, 0])

    # Patch
    patch = CSX.AddMetal('patch')
    patch.AddBox([-w/2, -l/2, h], [w/2, l/2, h])

    # Feed port through substrate at edge (y = -l/2, center of width)
    port = FDTD.AddLumpedPort(1, 50, [0, -l/2, 0], [0, -l/2, h], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_patch_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'patch.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "patch", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
