import os, tempfile, shutil, math
import numpy as np
from app.conductor import ConductorParams
from app.models import GroundPlaneParams

def simulate_ground_plane(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = GroundPlaneParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0      = p.frequency_mhz * 1e6
    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    res     = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad     = lambda0 / 4.0
    gap     = 2.0

    radial_len   = p.radial_length_mm
    angle_rad    = math.radians(p.radial_angle_deg)
    radial_x_end = radial_len * math.cos(angle_rad)
    radial_z_end = -radial_len * math.sin(angle_rad)  # downward from feed
    mono_len     = radial_len  # monopole same length as radials

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-radial_x_end - pad, -radial_x_end, 0, radial_x_end, radial_x_end + pad])
    mesh.AddLine('y', [-radial_x_end - pad, -radial_x_end, 0, radial_x_end, radial_x_end + pad])
    mesh.AddLine('z', [radial_z_end - pad, radial_z_end, 0, gap, mono_len + gap, mono_len + gap + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('ground_plane')
    # Monopole element
    metal.AddCylinder([0, 0, gap], [0, 0, mono_len + gap], radius)
    # Radials: equally spaced around the feed point
    for i in range(p.num_radials):
        theta = 2 * math.pi * i / p.num_radials
        end_x = radial_x_end * math.cos(theta)
        end_y = radial_x_end * math.sin(theta)
        metal.AddCylinder([0, 0, 0], [end_x, end_y, radial_z_end], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_gp_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'gp.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "ground_plane", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(), "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
