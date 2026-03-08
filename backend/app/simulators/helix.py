import os, tempfile, shutil, math
import numpy as np
from app.conductor import ConductorParams
from app.models import HelixParams

def simulate_helix(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = HelixParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = 2.0

    helix_r     = p.diameter_mm / 2.0
    total_h     = p.turns * p.pitch_mm
    steps_per_turn = 16
    total_steps = p.turns * steps_per_turn

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-helix_r - pad, -helix_r, 0, helix_r, helix_r + pad])
    mesh.AddLine('y', [-helix_r - pad, -helix_r, 0, helix_r, helix_r + pad])
    mesh.AddLine('z', [-pad, gap, total_h, total_h + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('helix')
    # Ground plane
    gp = CSX.AddMetal('gp')
    gp.AddBox([-helix_r - pad/2, -helix_r - pad/2, 0], [helix_r + pad/2, helix_r + pad/2, 0])

    # Helix winding
    for i in range(total_steps):
        theta1 = 2 * math.pi * i / steps_per_turn
        theta2 = 2 * math.pi * (i + 1) / steps_per_turn
        z1 = gap + (i / total_steps) * total_h
        z2 = gap + ((i + 1) / total_steps) * total_h
        p1 = [helix_r * math.cos(theta1), helix_r * math.sin(theta1), z1]
        p2 = [helix_r * math.cos(theta2), helix_r * math.sin(theta2), z2]
        metal.AddCylinder(p1, p2, radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_helix_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'helix.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "helix", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
