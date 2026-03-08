# backend/app/simulators/moxon.py
import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import MoxonParams

def simulate_moxon(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = MoxonParams(**params)

    try:
        import CSXCAD, openEMS
    except ImportError as e:
        raise

    f0     = p.frequency_mhz * 1e6
    A      = p.element_length_mm   # total width (mm)
    B      = p.tail_length_mm      # tail depth (mm)
    C      = p.feed_gap_mm         # feed gap (mm)
    radius = conductor.effective_radius_mm()

    c0         = 299792458.0
    lambda0    = c0 / f0 * 1000.0    # mm
    f_max      = f0 * 1.5
    lambda_min = c0 / f_max * 1000.0
    res        = lambda_min / 15.0

    # Gap between tail tips (Cebik: ~0.5% of wavelength)
    D     = max(lambda0 * 0.005, 1.0)
    depth = B + D + B

    FDTD = openEMS.openEMS(EndCriteria=5e-4, MaxTime=60)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    pad = lambda0 / 4.0

    mesh.AddLine('x', [-A/2 - pad, -A/2, -C/2, C/2, A/2, A/2 + pad])
    mesh.AddLine('y', [-pad, 0, B, B + D, depth, depth + pad])
    mesh.AddLine('z', [-pad - radius, 0, pad + radius])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('moxon')
    # Driven element halves
    metal.AddCylinder([-A/2, 0, 0], [-C/2, 0, 0], radius)
    metal.AddCylinder([ C/2, 0, 0], [ A/2, 0, 0], radius)
    # Driven element tails
    metal.AddCylinder([-A/2, 0, 0], [-A/2, B, 0], radius)
    metal.AddCylinder([ A/2, 0, 0], [ A/2, B, 0], radius)
    # Reflector
    metal.AddCylinder([-A/2, depth, 0], [A/2, depth, 0], radius)
    # Reflector tails
    metal.AddCylinder([-A/2, depth - B, 0], [-A/2, depth, 0], radius)
    metal.AddCylinder([ A/2, depth - B, 0], [ A/2, depth, 0], radius)

    # Feed port between driven element halves
    port = FDTD.AddLumpedPort(1, 50, [-C/2, 0, 0], [C/2, 0, 0], 'x', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_moxon_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'moxon.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {
            "antenna_type": "moxon",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist(),
            }
        }
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
