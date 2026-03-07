import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import SleeveParams

def simulate_sleeve(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = SleeveParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0         = p.frequency_mhz * 1e6
    c0         = 299792458.0
    lambda0    = c0 / f0 * 1000.0
    res        = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad        = lambda0 / 4.0
    gap        = 2.0
    sleeve_r   = radius * 4  # sleeve outer radius, 4x wire radius

    total_h = p.monopole_length_mm + gap

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-sleeve_r - pad, -sleeve_r, 0, sleeve_r, sleeve_r + pad])
    mesh.AddLine('y', [-sleeve_r - pad, -sleeve_r, 0, sleeve_r, sleeve_r + pad])
    mesh.AddLine('z', [-pad, 0, gap, p.sleeve_length_mm, total_h, total_h + pad])
    mesh.SmoothMeshLines('all', res)

    # Sleeve (coaxial outer conductor, bottom half)
    sleeve = CSX.AddMetal('sleeve')
    sleeve.AddCylinder([0, 0, 0], [0, 0, p.sleeve_length_mm], sleeve_r)

    # Monopole (inner conductor, full length above gap)
    mono = CSX.AddMetal('monopole')
    mono.AddCylinder([0, 0, gap], [0, 0, total_h], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_sleeve_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'sleeve.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "sleeve", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
