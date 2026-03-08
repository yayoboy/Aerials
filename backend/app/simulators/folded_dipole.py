import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import FoldedDipoleParams

def simulate_folded_dipole(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = FoldedDipoleParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    length  = p.length_mm
    spacing = p.spacing_mm
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = 2.0
    half    = length / 2.0

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-pad, -spacing/2, 0, spacing/2, pad])
    mesh.AddLine('y', [-pad, 0, pad])
    mesh.AddLine('z', [-half - pad, -half, -gap/2, gap/2, half, half + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('folded_dipole')
    # Driven element with feed gap
    metal.AddCylinder([-spacing/2, 0,  gap/2], [-spacing/2, 0,  half], radius)
    metal.AddCylinder([-spacing/2, 0, -gap/2], [-spacing/2, 0, -half], radius)
    # Return element (continuous)
    metal.AddCylinder([ spacing/2, 0, -half],  [ spacing/2, 0,  half], radius)
    # End bridges
    metal.AddCylinder([-spacing/2, 0,  half],  [ spacing/2, 0,  half], radius)
    metal.AddCylinder([-spacing/2, 0, -half],  [ spacing/2, 0, -half], radius)

    port = FDTD.AddLumpedPort(1, 300, [-spacing/2, 0, -gap/2],
                               [-spacing/2, 0, gap/2], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_foldeddipole_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'fd.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "folded_dipole", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(),
                            "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
