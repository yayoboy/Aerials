import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import JPoleParams

def simulate_jpole(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = JPoleParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = p.stub_spacing_mm  # feed gap = stub spacing

    long_len = p.long_element_mm
    stub_len = p.stub_length_mm
    spacing  = p.stub_spacing_mm

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-spacing - pad, -spacing, 0, spacing, spacing + pad])
    mesh.AddLine('y', [-pad, 0, pad])
    mesh.AddLine('z', [-pad, 0, stub_len, long_len, long_len + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('jpole')
    # Long element (left side): full height
    metal.AddCylinder([-spacing/2, 0, 0], [-spacing/2, 0, long_len], radius)
    # Short stub (right side): from 0 to stub_len
    metal.AddCylinder([ spacing/2, 0, 0], [ spacing/2, 0, stub_len], radius)
    # Bottom bridge connecting both elements
    metal.AddCylinder([-spacing/2, 0, 0], [spacing/2, 0, 0], radius)
    # Top bridge at stub_len height
    metal.AddCylinder([-spacing/2, 0, stub_len], [spacing/2, 0, stub_len], radius)

    # Feed port on the short stub side, near the bottom (about 1/4 up stub)
    feed_z = stub_len * 0.25
    port = FDTD.AddLumpedPort(1, 50, [spacing/2, 0, feed_z],
                               [-spacing/2, 0, feed_z], 'x', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_jpole_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'jpole.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "jpole", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
