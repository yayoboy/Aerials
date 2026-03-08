import os, tempfile, shutil, math
import numpy as np
from app.conductor import ConductorParams
from app.models import InvertedVParams

def simulate_inverted_v(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = InvertedVParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = 2.0

    arm_len = p.length_mm / 2.0
    half_angle_rad = math.radians(p.apex_angle_deg / 2.0)
    # Each arm goes from apex downward at half_angle from vertical
    arm_x = arm_len * math.sin(half_angle_rad)
    arm_z = arm_len * math.cos(half_angle_rad)
    apex_h = p.height_mm

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-arm_x - pad, -arm_x, 0, arm_x, arm_x + pad])
    mesh.AddLine('y', [-pad, 0, pad])
    mesh.AddLine('z', [-pad, 0, apex_h - arm_z, apex_h - gap/2, apex_h + gap/2, apex_h + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('inverted_v')
    # Left arm: from apex down-left
    metal.AddCylinder([0, 0, apex_h - gap/2], [-arm_x, 0, apex_h - arm_z], radius)
    # Right arm: from apex down-right
    metal.AddCylinder([0, 0, apex_h + gap/2], [ arm_x, 0, apex_h - arm_z], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, apex_h - gap/2], [0, 0, apex_h + gap/2], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_invertedv_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'iv.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "inverted_v", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
