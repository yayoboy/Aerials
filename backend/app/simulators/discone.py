import os, tempfile, shutil, math
import numpy as np
from app.conductor import ConductorParams
from app.models import DisconeParams

def simulate_discone(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = DisconeParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = 2.0

    cone_r   = p.cone_length_mm * math.sin(math.radians(p.cone_angle_deg))
    disc_r   = p.disc_diameter_mm / 2.0
    n_panels = 8
    half_angle_rad = math.radians(p.cone_angle_deg)

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    max_r = max(cone_r, disc_r)
    mesh.AddLine('x', [-max_r - pad, -max_r, 0, max_r, max_r + pad])
    mesh.AddLine('y', [-max_r - pad, -max_r, 0, max_r, max_r + pad])
    mesh.AddLine('z', [-pad, 0, gap, p.cone_length_mm, p.cone_length_mm + pad])
    mesh.SmoothMeshLines('all', res)

    # Disc (ground element) at z=0
    disc = CSX.AddMetal('disc')
    disc.AddBox([-disc_r, -disc_r, 0], [disc_r, disc_r, 0])

    # Cone approximated as N radial wires from apex downward
    cone = CSX.AddMetal('cone')
    for i in range(n_panels):
        theta = 2 * math.pi * i / n_panels
        tip_x = cone_r * math.cos(theta)
        tip_y = cone_r * math.sin(theta)
        cone.AddCylinder([0, 0, gap + p.cone_length_mm], [tip_x, tip_y, gap], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_discone_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'discone.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "discone", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
