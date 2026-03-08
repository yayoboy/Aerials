import os, tempfile, shutil, math
import numpy as np
from app.conductor import ConductorParams
from app.models import LoopParams

def simulate_loop(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = LoopParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = 2.0

    side = p.perimeter_mm / 4.0  # side length for square loop

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    half = side / 2.0
    mesh.AddLine('x', [-half - pad, -half, 0, half, half + pad])
    mesh.AddLine('y', [-pad, 0, pad])
    mesh.AddLine('z', [-half - pad, -half, -gap/2, gap/2, half, half + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('loop')
    # Bottom side (with feed gap)
    metal.AddCylinder([-half, 0, -half], [half, 0, -half], radius)   # bottom (no gap for square)
    metal.AddCylinder([ half, 0, -half], [half, 0,  half], radius)   # right
    metal.AddCylinder([-half, 0,  half], [half, 0,  half], radius)   # top
    # Left side with feed gap at z=0
    metal.AddCylinder([-half, 0, -half], [-half, 0, -gap/2], radius)
    metal.AddCylinder([-half, 0,  gap/2], [-half, 0,  half], radius)

    port = FDTD.AddLumpedPort(1, 50, [-half, 0, -gap/2], [-half, 0, gap/2], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_loop_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'loop.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "loop", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
