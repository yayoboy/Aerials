import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import YagiParams

def simulate_yagi(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = YagiParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    spacing = p.element_spacing_mm
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = 2.0

    z_ref    = 0.0
    z_driven = spacing
    n_dir    = len(p.director_lengths_mm)
    z_dirs   = [z_driven + (i + 1) * spacing for i in range(n_dir)]
    z_max    = z_dirs[-1] if z_dirs else z_driven
    max_half = max(p.reflector_length_mm, p.driven_length_mm,
                   *p.director_lengths_mm) / 2.0

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-max_half - pad, -max_half, 0, max_half, max_half + pad])
    mesh.AddLine('y', [-pad, 0, pad])
    mesh.AddLine('z', [z_ref - pad, z_ref, z_driven - gap/2, z_driven + gap/2,
                       z_max, z_max + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('yagi')
    # Reflector
    hr = p.reflector_length_mm / 2.0
    metal.AddCylinder([-hr, 0, z_ref], [hr, 0, z_ref], radius)
    # Driven element with gap
    hd = p.driven_length_mm / 2.0
    metal.AddCylinder([-hd, 0, z_driven], [-gap/2, 0, z_driven], radius)
    metal.AddCylinder([ gap/2, 0, z_driven], [ hd, 0, z_driven], radius)
    # Directors
    for i, dl in enumerate(p.director_lengths_mm):
        hdi = dl / 2.0
        metal.AddCylinder([-hdi, 0, z_dirs[i]], [hdi, 0, z_dirs[i]], radius)

    port = FDTD.AddLumpedPort(1, 50, [-gap/2, 0, z_driven],
                               [gap/2, 0, z_driven], 'x', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_yagi_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'yagi.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "yagi", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(),
                            "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
