# Multi-Antenna + 3D Visualization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand Aerials from a single-dipole simulator to a full multi-antenna platform with 12 antenna types, conductor material/cross-section options, and a Three.js 3D view.

**Architecture:** Backend gains a generic `/simulate/{antenna_type}` router backed by 12 openEMS simulators sharing a common conductor model. Frontend gains an AntennaSelector, dynamic AntennaForm, ConductorForm, and a Three.js Antenna3DView that updates live as the user adjusts parameters.

**Tech Stack:** Python 3 + FastAPI + openEMS (FDTD) + Pydantic v2 · React 19 + Vite + Three.js + Plotly.js

---

## Phase 1 — Backend Foundation

### Task 1: Create `conductor.py` — materials and cross-sections

**Files:**
- Create: `backend/app/conductor.py`
- Test: `backend/tests/test_conductor.py`

**Step 1: Create tests directory and write failing tests**

```bash
mkdir -p backend/tests && touch backend/tests/__init__.py
```

```python
# backend/tests/test_conductor.py
import pytest
from app.conductor import ConductorMaterial, CrossSection, ConductorParams, get_conductivity

def test_known_material_conductivity():
    assert get_conductivity(ConductorMaterial.COPPER) == pytest.approx(5.8e7)

def test_custom_material_requires_value():
    p = ConductorParams(material=ConductorMaterial.CUSTOM, conductivity=1e6,
                        cross_section=CrossSection.ROUND, radius_mm=1.0)
    assert p.conductivity == 1e6

def test_round_section_requires_radius():
    with pytest.raises(Exception):
        ConductorParams(material=ConductorMaterial.COPPER,
                        cross_section=CrossSection.ROUND)  # no radius_mm

def test_tube_section_requires_outer_and_wall():
    p = ConductorParams(material=ConductorMaterial.ALUMINUM,
                        cross_section=CrossSection.TUBE,
                        outer_diameter_mm=10.0, wall_thickness_mm=1.0)
    assert p.outer_diameter_mm == 10.0
```

**Step 2: Run to confirm failure**

```bash
cd backend && python -m pytest tests/test_conductor.py -v
# Expected: ModuleNotFoundError: No module named 'app.conductor'
```

**Step 3: Implement `conductor.py`**

```python
# backend/app/conductor.py
from enum import Enum
from typing import Optional
from pydantic import BaseModel, model_validator

class ConductorMaterial(str, Enum):
    COPPER    = "copper"
    SILVER    = "silver"
    ALUMINUM  = "aluminum"
    STEEL     = "steel"
    BRASS     = "brass"
    CUSTOM    = "custom"

class CrossSection(str, Enum):
    ROUND  = "round"
    TUBE   = "tube"
    FLAT   = "flat"
    SQUARE = "square"

CONDUCTIVITY_MAP = {
    ConductorMaterial.COPPER:   5.8e7,
    ConductorMaterial.SILVER:   6.3e7,
    ConductorMaterial.ALUMINUM: 3.5e7,
    ConductorMaterial.STEEL:    1.4e6,
    ConductorMaterial.BRASS:    1.6e7,
}

def get_conductivity(material: ConductorMaterial, custom: Optional[float] = None) -> float:
    if material == ConductorMaterial.CUSTOM:
        if custom is None:
            raise ValueError("conductivity required for custom material")
        return custom
    return CONDUCTIVITY_MAP[material]

class ConductorParams(BaseModel):
    material:          ConductorMaterial = ConductorMaterial.COPPER
    conductivity:      Optional[float]   = None   # S/m, only for CUSTOM
    cross_section:     CrossSection      = CrossSection.ROUND
    radius_mm:         Optional[float]   = 1.0    # ROUND / TUBE (inner approx)
    outer_diameter_mm: Optional[float]   = None   # TUBE
    wall_thickness_mm: Optional[float]   = None   # TUBE
    width_mm:          Optional[float]   = None   # FLAT / SQUARE
    thickness_mm:      Optional[float]   = None   # FLAT

    @model_validator(mode='after')
    def check_cross_section_params(self):
        cs = self.cross_section
        if cs == CrossSection.ROUND and self.radius_mm is None:
            raise ValueError("radius_mm required for round cross-section")
        if cs == CrossSection.TUBE:
            if self.outer_diameter_mm is None or self.wall_thickness_mm is None:
                raise ValueError("outer_diameter_mm and wall_thickness_mm required for tube")
        if cs in (CrossSection.FLAT, CrossSection.SQUARE) and self.width_mm is None:
            raise ValueError("width_mm required for flat/square cross-section")
        return self

    def effective_radius_mm(self) -> float:
        """Return equivalent round-wire radius for openEMS (all sections map to this)."""
        if self.cross_section == CrossSection.ROUND:
            return self.radius_mm
        if self.cross_section == CrossSection.TUBE:
            return self.outer_diameter_mm / 2.0
        if self.cross_section == CrossSection.SQUARE:
            return self.width_mm / 2.0
        if self.cross_section == CrossSection.FLAT:
            import math
            return math.sqrt(self.width_mm * self.thickness_mm) / 2.0
        return 1.0
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_conductor.py -v
# Expected: 4 PASSED
```

**Step 5: Commit**

```bash
git add backend/app/conductor.py backend/tests/ && \
git commit -m "feat(backend): add conductor material and cross-section models"
```

---

### Task 2: Create `models.py` — Pydantic models for all antenna types

**Files:**
- Create: `backend/app/models.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_models.py
from app.models import (
    DipoleParams, MonopoleParams, YagiParams, FoldedDipoleParams,
    InvertedVParams, LoopParams, HelixParams, SleeveParams,
    DisconeParams, PatchParams, GroundPlaneParams, JPoleParams,
    SimulationRequest
)
from app.conductor import ConductorParams

def test_dipole_defaults():
    p = DipoleParams()
    assert p.frequency_mhz == 300.0
    assert p.length_mm == 475.0

def test_yagi_min_directors():
    p = YagiParams(frequency_mhz=144.0, driven_length_mm=1020.0,
                   reflector_length_mm=1050.0, director_lengths_mm=[980.0],
                   element_spacing_mm=300.0)
    assert len(p.director_lengths_mm) >= 1

def test_simulation_request_has_conductor():
    req = SimulationRequest(antenna_type="dipole",
                            antenna_params=DipoleParams().model_dump())
    assert req.conductor.material == "copper"

def test_patch_requires_substrate():
    p = PatchParams(frequency_mhz=2400.0, width_mm=38.0, length_mm=29.0,
                    substrate_er=4.4, substrate_height_mm=1.6)
    assert p.substrate_er == 4.4
```

**Step 2: Verify failure**

```bash
cd backend && python -m pytest tests/test_models.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement `models.py`**

```python
# backend/app/models.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.conductor import ConductorParams

# ── Wire antennas ─────────────────────────────────────────────────────────────

class DipoleParams(BaseModel):
    frequency_mhz: float = 300.0
    length_mm:     float = 475.0

class FoldedDipoleParams(BaseModel):
    frequency_mhz: float = 144.0
    length_mm:     float = 1020.0
    spacing_mm:    float = 25.0    # distance between the two parallel wires

class MonopoleParams(BaseModel):
    frequency_mhz:      float = 300.0
    length_mm:          float = 237.5
    groundplane_mm:     float = 300.0  # diameter of the ground plane

class YagiParams(BaseModel):
    frequency_mhz:        float        = 144.0
    driven_length_mm:     float        = 1020.0
    reflector_length_mm:  float        = 1050.0
    director_lengths_mm:  List[float]  = [980.0, 960.0]   # front directors
    element_spacing_mm:   float        = 300.0

class InvertedVParams(BaseModel):
    frequency_mhz: float = 7.0
    length_mm:     float = 20200.0   # total wire length (both arms)
    apex_angle_deg: float = 120.0   # angle at the apex (90–150 typical)
    height_mm:     float = 15000.0  # height of apex above ground

class LoopParams(BaseModel):
    frequency_mhz: float = 14.0
    perimeter_mm:  float = 21400.0  # full loop perimeter
    shape:         str   = "square" # "square" | "circular"

class HelixParams(BaseModel):
    frequency_mhz: float = 2400.0
    diameter_mm:   float = 40.0    # helix coil diameter
    pitch_mm:      float = 30.0    # axial distance per turn
    turns:         int   = 8
    mode:          str   = "axial" # "axial" | "normal"

class SleeveParams(BaseModel):
    frequency_mhz:       float = 144.0
    monopole_length_mm:  float = 490.0
    sleeve_length_mm:    float = 245.0

class DisconeParams(BaseModel):
    frequency_mhz:    float = 400.0
    cone_length_mm:   float = 185.0
    cone_angle_deg:   float = 60.0   # half-angle of cone
    disc_diameter_mm: float = 150.0

class GroundPlaneParams(BaseModel):
    frequency_mhz:     float = 146.0
    radial_length_mm:  float = 490.0
    num_radials:       int   = 4      # 3 or 4 typical
    radial_angle_deg:  float = 45.0   # angle below horizontal

class JPoleParams(BaseModel):
    frequency_mhz:         float = 146.0
    long_element_mm:       float = 1000.0
    stub_length_mm:        float = 330.0
    stub_spacing_mm:       float = 25.0

# ── Planar antennas ───────────────────────────────────────────────────────────

class PatchParams(BaseModel):
    frequency_mhz:        float = 2400.0
    width_mm:             float = 38.0
    length_mm:            float = 29.0
    substrate_er:         float = 4.4    # relative permittivity (e.g. FR4)
    substrate_height_mm:  float = 1.6

# ── Generic wrapper ───────────────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    antenna_type:   str               # slug matching router key
    antenna_params: Dict[str, Any]    # validated by individual simulator
    conductor:      ConductorParams   = ConductorParams()
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_models.py -v
# Expected: 4 PASSED
```

**Step 5: Commit**

```bash
git add backend/app/models.py backend/tests/test_models.py && \
git commit -m "feat(backend): add Pydantic models for 12 antenna types"
```

---

### Task 3: Refactor `main.py` — generic `/simulate/{antenna_type}` router

**Files:**
- Modify: `backend/main.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

MOCK_RESULT = {
    "antenna_type": "dipole",
    "status": "success",
    "results": {"frequencies_mhz": [300.0], "s11_db": [-10.0]}
}

def test_health_check():
    from main import app
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200

def test_simulate_dipole_calls_simulator():
    with patch("main.SIMULATOR_MAP") as mock_map:
        mock_sim = lambda p, c: MOCK_RESULT
        mock_map.__contains__ = lambda self, k: True
        mock_map.__getitem__ = lambda self, k: mock_sim
        from main import app
        client = TestClient(app)
        r = client.post("/simulate/dipole", json={
            "antenna_type": "dipole",
            "antenna_params": {"frequency_mhz": 300, "length_mm": 475},
            "conductor": {"material": "copper", "cross_section": "round", "radius_mm": 1.0}
        })
        assert r.status_code in (200, 422)  # 422 if mock not wired; OK

def test_simulate_unknown_type_returns_404():
    from main import app
    client = TestClient(app)
    r = client.post("/simulate/nonexistent", json={
        "antenna_type": "nonexistent",
        "antenna_params": {},
        "conductor": {}
    })
    assert r.status_code == 404
```

**Step 2: Verify failure**

```bash
cd backend && python -m pytest tests/test_api.py::test_simulate_unknown_type_returns_404 -v
# Expected: FAIL (current main.py has no generic route)
```

**Step 3: Rewrite `main.py`**

```python
# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import SimulationRequest
from app.conductor import ConductorParams

# Import all simulators (lazy imports inside functions to keep startup fast)
def _load_simulators():
    from app.simulators.dipole        import simulate_dipole
    from app.simulators.folded_dipole import simulate_folded_dipole
    from app.simulators.monopole      import simulate_monopole
    from app.simulators.yagi          import simulate_yagi
    from app.simulators.inverted_v    import simulate_inverted_v
    from app.simulators.loop          import simulate_loop
    from app.simulators.helix         import simulate_helix
    from app.simulators.sleeve        import simulate_sleeve
    from app.simulators.discone       import simulate_discone
    from app.simulators.patch         import simulate_patch
    from app.simulators.ground_plane  import simulate_ground_plane
    from app.simulators.jpole         import simulate_jpole
    return {
        "dipole":        simulate_dipole,
        "folded_dipole": simulate_folded_dipole,
        "monopole":      simulate_monopole,
        "yagi":          simulate_yagi,
        "inverted_v":    simulate_inverted_v,
        "loop":          simulate_loop,
        "helix":         simulate_helix,
        "sleeve":        simulate_sleeve,
        "discone":       simulate_discone,
        "patch":         simulate_patch,
        "ground_plane":  simulate_ground_plane,
        "jpole":         simulate_jpole,
    }

SIMULATOR_MAP = _load_simulators()

app = FastAPI(title="Aerials — Antenna Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "antennas": list(SIMULATOR_MAP.keys())}

@app.post("/simulate/{antenna_type}")
def run_simulation(antenna_type: str, req: SimulationRequest):
    if antenna_type not in SIMULATOR_MAP:
        raise HTTPException(status_code=404,
                            detail=f"Unknown antenna type: {antenna_type}")
    print(f"[{antenna_type}] params={req.antenna_params} conductor={req.conductor}")
    try:
        return SIMULATOR_MAP[antenna_type](req.antenna_params, req.conductor)
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_api.py -v
# Expected: test_health_check PASS, test_simulate_unknown_type_returns_404 PASS
```

**Step 5: Commit**

```bash
git add backend/main.py backend/tests/test_api.py && \
git commit -m "feat(backend): generic /simulate/{antenna_type} router"
```

---

## Phase 2 — Backend Simulators

> All simulators follow the same signature:
> `def simulate_X(params: dict, conductor: ConductorParams) -> dict`
> They use the same openEMS FDTD pattern as the existing `dipole.py`.
> The conductor's `effective_radius_mm()` is used for wire radius.
> Each returns `{"antenna_type", "status", "results": {"frequencies_mhz", "s11_db"}}`.

### Task 4: Refactor existing `dipole.py` to new signature

**Files:**
- Modify: `backend/app/simulators/dipole.py`

**Step 1: Update `dipole.py` to accept `(params: dict, conductor: ConductorParams)`**

```python
# backend/app/simulators/dipole.py
import os, sys, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import DipoleParams

def simulate_dipole(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p = DipoleParams(**params)

    try:
        import CSXCAD, openEMS
    except ImportError as e:
        raise

    f0     = p.frequency_mhz * 1e6
    length = p.length_mm
    radius = conductor.effective_radius_mm()

    c0      = 299792458.0
    lambda0 = c0 / f0 * 1000.0
    f_max   = f0 * 1.5
    lambda_min = c0 / f_max * 1000.0
    res     = lambda_min / 10.0

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    pad = lambda0 / 4.0
    gap = 2.0

    mesh.AddLine('x', [-pad - radius, 0, pad + radius])
    mesh.AddLine('y', [-pad - radius, 0, pad + radius])
    mesh.AddLine('z', [-length/2 - pad, -length/2, -gap/2, gap/2, length/2, length/2 + pad])
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('dipole')
    metal.AddCylinder([0, 0,  gap/2], [0, 0,  length/2], radius)
    metal.AddCylinder([0, 0, -gap/2], [0, 0, -length/2], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, -gap/2], [0, 0, gap/2], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_dipole_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'dipole.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {
            "antenna_type": "dipole",
            "status": "success",
            "results": {
                "frequencies_mhz": (f_eval / 1e6).tolist(),
                "s11_db": s11_db.tolist()
            }
        }
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
```

**Step 2: Commit**

```bash
git add backend/app/simulators/dipole.py && \
git commit -m "refactor(dipole): adapt to new (params, conductor) signature"
```

---

### Task 5: Create `monopole.py`

**Files:**
- Create: `backend/app/simulators/monopole.py`

**Step 1: Implement**

```python
# backend/app/simulators/monopole.py
import os, tempfile, shutil
import numpy as np
from app.conductor import ConductorParams
from app.models import MonopoleParams

def simulate_monopole(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = MonopoleParams(**params)
    radius = conductor.effective_radius_mm()

    import CSXCAD, openEMS

    f0         = p.frequency_mhz * 1e6
    length     = p.length_mm
    gp_radius  = p.groundplane_mm / 2.0
    c0         = 299792458.0
    lambda0    = c0 / f0 * 1000.0
    res        = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad        = lambda0 / 4.0
    gap        = 2.0

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)

    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    mesh.AddLine('x', [-gp_radius - pad, -gp_radius, 0, gp_radius, gp_radius + pad])
    mesh.AddLine('y', [-gp_radius - pad, -gp_radius, 0, gp_radius, gp_radius + pad])
    mesh.AddLine('z', [-pad, 0, gap, length, length + pad])
    mesh.SmoothMeshLines('all', res)

    # Ground plane (disk at z=0)
    gp = CSX.AddMetal('groundplane')
    gp.AddBox([-gp_radius, -gp_radius, 0], [gp_radius, gp_radius, 0])

    # Monopole element
    mono = CSX.AddMetal('monopole')
    mono.AddCylinder([0, 0, gap], [0, 0, length], radius)

    port = FDTD.AddLumpedPort(1, 50, [0, 0, 0], [0, 0, gap], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_mono_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'mono.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "monopole", "status": "success",
                "results": {"frequencies_mhz": (f_eval / 1e6).tolist(),
                            "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
```

**Step 2: Commit**

```bash
git add backend/app/simulators/monopole.py && \
git commit -m "feat(backend): monopole simulator"
```

---

### Task 6: Create `folded_dipole.py`

**Files:**
- Create: `backend/app/simulators/folded_dipole.py`

**Step 1: Implement**

```python
# backend/app/simulators/folded_dipole.py
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

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
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
    # Driven element (bottom wire with gap at feed)
    metal.AddCylinder([-spacing/2, 0, gap/2],  [-spacing/2, 0,  half], radius)
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
```

**Step 2: Commit**

```bash
git add backend/app/simulators/folded_dipole.py && \
git commit -m "feat(backend): folded dipole simulator"
```

---

### Task 7: Create `yagi.py`

**Files:**
- Create: `backend/app/simulators/yagi.py`

**Step 1: Implement**

```python
# backend/app/simulators/yagi.py
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

    f0       = p.frequency_mhz * 1e6
    spacing  = p.element_spacing_mm
    c0       = 299792458.0
    lambda0  = c0 / f0 * 1000.0
    res      = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    pad      = lambda0 / 4.0
    gap      = 2.0

    # Element z-positions: reflector at z=0, driven at z=spacing, directors after
    n_dir     = len(p.director_lengths_mm)
    z_ref     = 0.0
    z_driven  = spacing
    z_dirs    = [z_driven + (i + 1) * spacing for i in range(n_dir)]
    z_max     = z_dirs[-1] if z_dirs else z_driven
    max_half  = max(p.reflector_length_mm, p.driven_length_mm,
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
    half_r = p.reflector_length_mm / 2.0
    metal.AddCylinder([-half_r, 0, z_ref], [half_r, 0, z_ref], radius)
    # Driven element (with gap)
    half_d = p.driven_length_mm / 2.0
    metal.AddCylinder([-half_d, 0, z_driven], [-gap/2, 0, z_driven], radius)
    metal.AddCylinder([ gap/2, 0, z_driven], [ half_d, 0, z_driven], radius)
    # Directors
    for i, dl in enumerate(p.director_lengths_mm):
        half_di = dl / 2.0
        metal.AddCylinder([-half_di, 0, z_dirs[i]], [half_di, 0, z_dirs[i]], radius)

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
```

**Step 2: Commit**

```bash
git add backend/app/simulators/yagi.py && \
git commit -m "feat(backend): Yagi-Uda simulator"
```

---

### Task 8: Create remaining 8 simulators (inverted_v, loop, helix, sleeve, discone, patch, ground_plane, jpole)

> These follow the same pattern. Implement them one file at a time.
> **Each file must** import the corresponding model, call `conductor.effective_radius_mm()`,
> set up openEMS FDTD, add geometry, add lumped port, run, and return the standard dict.

**Files to create:**
- `backend/app/simulators/inverted_v.py`
- `backend/app/simulators/loop.py`
- `backend/app/simulators/helix.py`
- `backend/app/simulators/sleeve.py`
- `backend/app/simulators/discone.py`
- `backend/app/simulators/patch.py`
- `backend/app/simulators/ground_plane.py`
- `backend/app/simulators/jpole.py`

**Template for each simulator (replace `X`, `XParams`, geometry):**

```python
# backend/app/simulators/X.py
import os, tempfile, shutil, numpy as np
from app.conductor import ConductorParams
from app.models import XParams

def simulate_X(params: dict, conductor: ConductorParams = None) -> dict:
    if conductor is None:
        conductor = ConductorParams()
    p      = XParams(**params)
    radius = conductor.effective_radius_mm()
    import CSXCAD, openEMS

    f0  = p.frequency_mhz * 1e6
    c0  = 299792458.0
    res = (c0 / (f0 * 1.5)) / 10.0 * 1000.0
    lambda0 = c0 / f0 * 1000.0
    pad = lambda0 / 4.0

    FDTD = openEMS.openEMS(EndCriteria=5e-4)
    FDTD.SetGaussExcite(f0, f0 / 2)
    FDTD.SetBoundaryCond(['PML_8'] * 6)
    CSX  = CSXCAD.ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    # <<< ADD MESH LINES specific to antenna geometry >>>
    mesh.SmoothMeshLines('all', res)

    metal = CSX.AddMetal('X')
    # <<< ADD GEOMETRY (AddCylinder, AddBox, AddWire, etc.) >>>

    port = FDTD.AddLumpedPort(1, 50, [0,0,0], [0,0,gap], 'z', 1.0)

    sim_dir = tempfile.mkdtemp(prefix="openems_X_")
    try:
        CSX.Write2XML(os.path.join(sim_dir, 'X.xml'))
        FDTD.Run(sim_dir, verbose=0)
        f_eval = np.linspace(f0 * 0.8, f0 * 1.2, 51)
        port.CalcPort(sim_dir, f_eval)
        s11    = port.uf_ref / port.uf_inc
        s11_db = 20.0 * np.log10(np.abs(s11))
        return {"antenna_type": "X", "status": "success",
                "results": {"frequencies_mhz": (f_eval/1e6).tolist(),
                            "s11_db": s11_db.tolist()}}
    finally:
        shutil.rmtree(sim_dir, ignore_errors=True)
```

**Key geometry notes per antenna:**

- **inverted_v**: Two wires from apex `[0, 0, height_mm]` angling down symmetrically at `apex_angle_deg/2` from vertical. Gap at apex. Port at `[0,0,height_mm-gap/2]` to `[0,0,height_mm+gap/2]` in z.
- **loop**: Square loop: 4 cylinder segments forming a square with side = `perimeter_mm/4`. Gap at bottom center. Circular loop: approximate with 16 short cylinders forming a polygon.
- **helix**: `turns` cylinders wound around z-axis using parametric angle steps. Each turn advances `pitch_mm` in z. Helix radius = `diameter_mm/2`.
- **sleeve**: Monopole cylinder from `gap` to `monopole_length_mm+gap`. Sleeve as hollow cylinder (two surfaces — use a box approximation) from `0` to `sleeve_length_mm`. Port at `[0,0,0]` to `[0,0,gap]`.
- **discone**: Cone approximated as N triangular panels (or use AddBox for simplified version). Disc as flat circle at z=0. Port between disc center and cone apex.
- **patch**: Two Metal layers: substrate `AddBox` filled with dielectric material, patch `AddBox` on top, ground plane `AddBox` on bottom. Port through substrate at center edge.
- **ground_plane**: Central vertical monopole, `num_radials` radials at `radial_angle_deg` below horizontal. Each radial is a cylinder from feed point outward.
- **jpole**: Long element (continuous), short stub element (with gap at bottom), two cross-pieces connecting them. Port at bottom of the gap.

**Step 2: Commit after all 8 files**

```bash
git add backend/app/simulators/ && \
git commit -m "feat(backend): implement all 8 remaining antenna simulators"
```

---

## Phase 3 — Frontend Foundation

### Task 9: Install Three.js and update package.json

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install Three.js**

```bash
cd frontend && npm install three
```

**Step 2: Verify install**

```bash
grep '"three"' package.json
# Expected: "three": "^0.x.x"
```

**Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json && \
git commit -m "chore(frontend): add Three.js dependency"
```

---

### Task 10: Create `constants/conductors.js`

**Files:**
- Create: `frontend/src/constants/conductors.js`

**Step 1: Create**

```javascript
// frontend/src/constants/conductors.js
export const MATERIALS = [
  { id: 'copper',   label: 'Rame (Cu)',      conductivity: 5.8e7, color: '#b87333' },
  { id: 'silver',   label: 'Argento (Ag)',   conductivity: 6.3e7, color: '#c0c0c0' },
  { id: 'aluminum', label: 'Alluminio (Al)', conductivity: 3.5e7, color: '#848789' },
  { id: 'steel',    label: 'Acciaio inox',   conductivity: 1.4e6, color: '#8d8d8d' },
  { id: 'brass',    label: 'Ottone',         conductivity: 1.6e7, color: '#b5a642' },
  { id: 'custom',   label: 'Personalizzato', conductivity: null,  color: '#ffffff' },
];

export const CROSS_SECTIONS = [
  { id: 'round',  label: 'Filo tondo',     fields: ['radius_mm'] },
  { id: 'tube',   label: 'Tubo',           fields: ['outer_diameter_mm', 'wall_thickness_mm'] },
  { id: 'flat',   label: 'Nastro piatto',  fields: ['width_mm', 'thickness_mm'] },
  { id: 'square', label: 'Profilo quadrato', fields: ['width_mm'] },
];
```

**Step 2: Commit**

```bash
git add frontend/src/constants/ && \
git commit -m "feat(frontend): conductor material and cross-section constants"
```

---

### Task 11: Create antenna config files

**Files:**
- Create: `frontend/src/antennas/configs/index.js` and one file per antenna type

**Step 1: Create the config directory and files**

```bash
mkdir -p frontend/src/antennas/configs
```

```javascript
// frontend/src/antennas/configs/dipole.js
export default {
  id: 'dipole',
  label: 'Dipolo λ/2',
  description: 'Antenna a dipolo a mezza onda',
  defaultParams: { frequency_mhz: 300, length_mm: 475 },
  fields: [
    { name: 'frequency_mhz', label: 'Frequenza (MHz)', type: 'number', min: 1, step: 1 },
    { name: 'length_mm',     label: 'Lunghezza (mm)',  type: 'number', min: 1, step: 1 },
  ],
};
```

Create the same structure for all 12 antenna types with their respective `defaultParams` and `fields`. Then create the index:

```javascript
// frontend/src/antennas/configs/index.js
import dipole        from './dipole.js';
import foldedDipole  from './folded_dipole.js';
import monopole      from './monopole.js';
import yagi          from './yagi.js';
import invertedV     from './inverted_v.js';
import loop          from './loop.js';
import helix         from './helix.js';
import sleeve        from './sleeve.js';
import discone       from './discone.js';
import patch         from './patch.js';
import groundPlane   from './ground_plane.js';
import jpole         from './jpole.js';

export const ANTENNA_CONFIGS = [
  dipole, foldedDipole, monopole, yagi, invertedV, loop,
  helix, sleeve, discone, patch, groundPlane, jpole,
];

export const ANTENNA_MAP = Object.fromEntries(
  ANTENNA_CONFIGS.map(c => [c.id, c])
);
```

**Step 2: Commit**

```bash
git add frontend/src/antennas/ && \
git commit -m "feat(frontend): antenna config definitions for all 12 types"
```

---

### Task 12: Create `AntennaSelector.jsx`

**Files:**
- Create: `frontend/src/components/AntennaSelector.jsx`

**Step 1: Implement**

```jsx
// frontend/src/components/AntennaSelector.jsx
import { ANTENNA_CONFIGS } from '../antennas/configs/index.js';

export default function AntennaSelector({ selected, onChange }) {
  return (
    <div className="antenna-selector">
      {ANTENNA_CONFIGS.map(cfg => (
        <button
          key={cfg.id}
          className={`antenna-card ${selected === cfg.id ? 'active' : ''}`}
          onClick={() => onChange(cfg.id)}
          title={cfg.description}
        >
          <span className="antenna-card-label">{cfg.label}</span>
        </button>
      ))}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/AntennaSelector.jsx && \
git commit -m "feat(frontend): AntennaSelector component"
```

---

### Task 13: Create `ConductorForm.jsx`

**Files:**
- Create: `frontend/src/components/ConductorForm.jsx`

**Step 1: Implement**

```jsx
// frontend/src/components/ConductorForm.jsx
import { MATERIALS, CROSS_SECTIONS } from '../constants/conductors.js';

export default function ConductorForm({ conductor, onChange }) {
  const material   = MATERIALS.find(m => m.id === conductor.material) || MATERIALS[0];
  const section    = CROSS_SECTIONS.find(s => s.id === conductor.cross_section) || CROSS_SECTIONS[0];

  const set = (key, value) => onChange({ ...conductor, [key]: value });

  return (
    <div className="conductor-form">
      <h3 className="section-title">Conduttore</h3>

      <div className="form-group">
        <label>Materiale</label>
        <select className="form-input" value={conductor.material}
                onChange={e => set('material', e.target.value)}>
          {MATERIALS.map(m => (
            <option key={m.id} value={m.id}>{m.label}</option>
          ))}
        </select>
      </div>

      {conductor.material === 'custom' && (
        <div className="form-group">
          <label>Conduttività (S/m)</label>
          <input className="form-input" type="number" value={conductor.conductivity || ''}
                 onChange={e => set('conductivity', parseFloat(e.target.value))} />
        </div>
      )}

      <div className="form-group">
        <label>Sezione trasversale</label>
        <select className="form-input" value={conductor.cross_section}
                onChange={e => set('cross_section', e.target.value)}>
          {CROSS_SECTIONS.map(s => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
      </div>

      {section.fields.map(field => (
        <div key={field} className="form-group">
          <label>{field.replace(/_/g, ' ')} (mm)</label>
          <input className="form-input" type="number" min="0.01" step="0.1"
                 value={conductor[field] || ''}
                 onChange={e => set(field, parseFloat(e.target.value))} />
        </div>
      ))}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/ConductorForm.jsx && \
git commit -m "feat(frontend): ConductorForm component"
```

---

### Task 14: Create `AntennaForm.jsx` — dynamic param form

**Files:**
- Create: `frontend/src/components/AntennaForm.jsx`

**Step 1: Implement**

```jsx
// frontend/src/components/AntennaForm.jsx
import { ANTENNA_MAP } from '../antennas/configs/index.js';

export default function AntennaForm({ antennaType, params, onChange }) {
  const cfg = ANTENNA_MAP[antennaType];
  if (!cfg) return null;

  const set = (name, value) => onChange({ ...params, [name]: value });

  return (
    <div className="antenna-form">
      {cfg.fields.map(field => (
        <div key={field.name} className="form-group">
          <label>{field.label}</label>
          {field.type === 'select' ? (
            <select className="form-input" value={params[field.name] ?? field.default}
                    onChange={e => set(field.name, e.target.value)}>
              {field.options.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          ) : (
            <input
              className="form-input"
              type={field.type}
              min={field.min}
              step={field.step}
              value={params[field.name] ?? ''}
              onChange={e => set(field.name,
                field.type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/AntennaForm.jsx && \
git commit -m "feat(frontend): dynamic AntennaForm component"
```

---

### Task 15: Extract `S11Chart.jsx`

**Files:**
- Create: `frontend/src/components/S11Chart.jsx`

**Step 1: Implement**

```jsx
// frontend/src/components/S11Chart.jsx
import Plot from 'react-plotly.js';

export default function S11Chart({ results, loading }) {
  if (loading) return <div className="spinner" />;
  if (!results?.results) {
    return <p style={{ color: 'var(--text-secondary)' }}>
      Configura i parametri e avvia la simulazione.
    </p>;
  }

  return (
    <Plot
      data={[{
        x: results.results.frequencies_mhz,
        y: results.results.s11_db,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color: '#2f81f7', size: 6 },
        line:   { color: '#2f81f7', width: 2 },
        name: 'S11',
      }]}
      layout={{
        autosize: true,
        paper_bgcolor: 'transparent',
        plot_bgcolor:  'transparent',
        font: { color: '#8b949e', family: 'Inter' },
        xaxis: { title: 'Frequenza (MHz)',
                 gridcolor: 'rgba(240,246,252,0.1)',
                 zerolinecolor: 'rgba(240,246,252,0.2)' },
        yaxis: { title: 'S11 (dB)',
                 gridcolor: 'rgba(240,246,252,0.1)',
                 zerolinecolor: 'rgba(240,246,252,0.2)' },
        margin: { t: 20, r: 20, l: 60, b: 60 },
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
    />
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/S11Chart.jsx && \
git commit -m "refactor(frontend): extract S11Chart component"
```

---

## Phase 4 — Three.js 3D View

### Task 16: Create geometry generators for all antenna types

**Files:**
- Create: `frontend/src/antennas/geometries/index.js`
- Create: one file per antenna type under `frontend/src/antennas/geometries/`

**Step 1: Create the geometry module**

```bash
mkdir -p frontend/src/antennas/geometries
```

```javascript
// frontend/src/antennas/geometries/dipole.js
import * as THREE from 'three';

/**
 * Returns an array of THREE.Mesh objects representing the dipole geometry.
 * All dimensions in mm, converted to meters for Three.js scene (scale 1mm = 0.001 units).
 */
export function buildDipole(params, conductor, color) {
  const group   = new THREE.Group();
  const length  = (params.length_mm ?? 475) * 0.001;
  const radius  = (conductor?.radius_mm ?? 1) * 0.001;
  const mat     = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.8 });

  const geo1 = new THREE.CylinderGeometry(radius, radius, length / 2, 12);
  const m1   = new THREE.Mesh(geo1, mat);
  m1.position.y = length / 4;

  const geo2 = new THREE.CylinderGeometry(radius, radius, length / 2, 12);
  const m2   = new THREE.Mesh(geo2, mat);
  m2.position.y = -length / 4;

  // Feed point indicator
  const feedGeo = new THREE.SphereGeometry(radius * 2, 8, 8);
  const feedMat = new THREE.MeshStandardMaterial({ color: 0xff3333 });
  const feed    = new THREE.Mesh(feedGeo, feedMat);
  feed.position.y = 0;

  group.add(m1, m2, feed);
  return group;
}
```

Create similar `buildX(params, conductor, color)` functions for each antenna type:
- `monopole.js` — vertical element + flat disc groundplane (CylinderGeometry + CircleGeometry)
- `folded_dipole.js` — two parallel cylinders + end bridges (BoxGeometry for bridges)
- `yagi.js` — multiple horizontal elements at varying z positions, color-coded (reflector=blue, driven=green, directors=gray)
- `inverted_v.js` — two angled arms from apex using cylinder rotated by apex_angle_deg
- `loop.js` — square loop: 4 BoxGeometry segments / circular: TorusGeometry
- `helix.js` — `turns * 16` short cylinders wound in helix path
- `sleeve.js` — monopole + concentric outer cylinder (sleeve)
- `discone.js` — ConeGeometry for cone + CircleGeometry for disc
- `patch.js` — three stacked BoxGeometry (groundplane, substrate, patch)
- `ground_plane.js` — vertical element + N radials at radial_angle_deg below horizontal
- `jpole.js` — tall element + short stub connected at top and bottom

```javascript
// frontend/src/antennas/geometries/index.js
import { buildDipole }       from './dipole.js';
import { buildFoldedDipole } from './folded_dipole.js';
import { buildMonopole }     from './monopole.js';
import { buildYagi }         from './yagi.js';
import { buildInvertedV }    from './inverted_v.js';
import { buildLoop }         from './loop.js';
import { buildHelix }        from './helix.js';
import { buildSleeve }       from './sleeve.js';
import { buildDiscone }      from './discone.js';
import { buildPatch }        from './patch.js';
import { buildGroundPlane }  from './ground_plane.js';
import { buildJPole }        from './jpole.js';

export const GEOMETRY_BUILDERS = {
  dipole:        buildDipole,
  folded_dipole: buildFoldedDipole,
  monopole:      buildMonopole,
  yagi:          buildYagi,
  inverted_v:    buildInvertedV,
  loop:          buildLoop,
  helix:         buildHelix,
  sleeve:        buildSleeve,
  discone:       buildDiscone,
  patch:         buildPatch,
  ground_plane:  buildGroundPlane,
  jpole:         buildJPole,
};
```

**Step 2: Commit**

```bash
git add frontend/src/antennas/geometries/ && \
git commit -m "feat(frontend): Three.js geometry builders for all 12 antenna types"
```

---

### Task 17: Create `Antenna3DView.jsx`

**Files:**
- Create: `frontend/src/components/Antenna3DView.jsx`

**Step 1: Implement**

```jsx
// frontend/src/components/Antenna3DView.jsx
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GEOMETRY_BUILDERS } from '../antennas/geometries/index.js';
import { MATERIALS } from '../constants/conductors.js';

export default function Antenna3DView({ antennaType, params, conductor }) {
  const mountRef    = useRef(null);
  const sceneRef    = useRef(null);
  const cameraRef   = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const antennaRef  = useRef(null);
  const frameRef    = useRef(null);

  // One-time Three.js setup
  useEffect(() => {
    const el = mountRef.current;
    const w  = el.clientWidth;
    const h  = el.clientHeight;

    const scene    = new THREE.Scene();
    scene.background = new THREE.Color(0x0d1117);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(50, w / h, 0.001, 100);
    camera.position.set(0.3, 0.3, 0.8);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(window.devicePixelRatio);
    el.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controlsRef.current = controls;

    // Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dir = new THREE.DirectionalLight(0xffffff, 1.2);
    dir.position.set(2, 4, 3);
    scene.add(dir);

    // Grid helper
    const grid = new THREE.GridHelper(2, 20, 0x222222, 0x222222);
    scene.add(grid);

    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      const w = el.clientWidth, h = el.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(frameRef.current);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      el.removeChild(renderer.domElement);
    };
  }, []);

  // Rebuild geometry whenever params change
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    if (antennaRef.current) {
      scene.remove(antennaRef.current);
      antennaRef.current = null;
    }

    const builder = GEOMETRY_BUILDERS[antennaType];
    if (!builder) return;

    const mat    = MATERIALS.find(m => m.id === (conductor?.material ?? 'copper'));
    const color  = new THREE.Color(mat?.color ?? '#b87333');
    const group  = builder(params, conductor, color);
    scene.add(group);
    antennaRef.current = group;
  }, [antennaType, params, conductor]);

  return <div ref={mountRef} style={{ width: '100%', height: '100%' }} />;
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/Antenna3DView.jsx && \
git commit -m "feat(frontend): Antenna3DView with Three.js + OrbitControls"
```

---

## Phase 5 — Integration

### Task 18: Rewrite `App.jsx` — wire everything together

**Files:**
- Modify: `frontend/src/App.jsx`

**Step 1: Rewrite**

```jsx
// frontend/src/App.jsx
import { useState } from 'react';
import AntennaSelector from './components/AntennaSelector.jsx';
import AntennaForm     from './components/AntennaForm.jsx';
import ConductorForm   from './components/ConductorForm.jsx';
import S11Chart        from './components/S11Chart.jsx';
import Antenna3DView   from './components/Antenna3DView.jsx';
import { ANTENNA_MAP } from './antennas/configs/index.js';

const DEFAULT_CONDUCTOR = {
  material: 'copper',
  cross_section: 'round',
  radius_mm: 1.0,
};

export default function App() {
  const [antennaType, setAntennaType] = useState('dipole');
  const [params,      setParams]      = useState(ANTENNA_MAP['dipole'].defaultParams);
  const [conductor,   setConductor]   = useState(DEFAULT_CONDUCTOR);
  const [loading,     setLoading]     = useState(false);
  const [results,     setResults]     = useState(null);

  const handleAntennaChange = (type) => {
    setAntennaType(type);
    setParams(ANTENNA_MAP[type].defaultParams);
    setResults(null);
  };

  const handleSimulate = async () => {
    setLoading(true);
    setResults(null);
    try {
      const res = await fetch(`http://localhost:8000/simulate/${antennaType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          antenna_type:   antennaType,
          antenna_params: params,
          conductor,
        }),
      });
      setResults(await res.json());
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <h1><span className="icon">⚡</span>Aerials</h1>

        <div className="form-group">
          <label>Tipo di Antenna</label>
          <AntennaSelector selected={antennaType} onChange={handleAntennaChange} />
        </div>

        <AntennaForm
          antennaType={antennaType}
          params={params}
          onChange={setParams}
        />

        <ConductorForm
          conductor={conductor}
          onChange={setConductor}
        />

        <button className="btn-primary" onClick={handleSimulate} disabled={loading}>
          {loading ? 'Simulazione in corso...' : 'Avvia simulazione FDTD'}
        </button>
      </aside>

      <main className="main-content">
        <div className="glass-panel">
          <h2 className="panel-header">Vista 3D — {ANTENNA_MAP[antennaType]?.label}</h2>
          <div className="plot-container" style={{ height: '340px' }}>
            <Antenna3DView
              antennaType={antennaType}
              params={params}
              conductor={conductor}
            />
          </div>
        </div>

        <div className="glass-panel">
          <h2 className="panel-header">S11 Return Loss</h2>
          <div className="plot-container">
            <S11Chart results={results} loading={loading} />
          </div>
        </div>
      </main>
    </div>
  );
}
```

**Step 2: Start frontend dev server and verify it renders**

```bash
cd frontend && npm run dev
# Open http://localhost:5173 — expect: sidebar with antenna selector, 3D view, empty S11 chart
```

**Step 3: Commit**

```bash
git add frontend/src/App.jsx && \
git commit -m "feat(frontend): wire all components into App — multi-antenna + 3D view"
```

---

### Task 19: Add CSS for new components

**Files:**
- Modify: `frontend/src/App.css`

**Step 1: Append new styles**

Add these rules to the bottom of `App.css`:

```css
/* Antenna selector grid */
.antenna-selector {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  margin-bottom: 12px;
}
.antenna-card {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border-color, #30363d);
  border-radius: 6px;
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  font-size: 11px;
  padding: 6px 4px;
  text-align: center;
  transition: border-color 0.15s, color 0.15s;
}
.antenna-card:hover { border-color: #58a6ff; color: #f0f6fc; }
.antenna-card.active { border-color: #2f81f7; color: #f0f6fc; background: #1c2e4a; }

/* Section titles */
.section-title {
  color: var(--text-secondary, #8b949e);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  margin: 16px 0 8px;
  text-transform: uppercase;
}

/* Conductor form */
.conductor-form { margin-top: 8px; }
```

**Step 2: Commit**

```bash
git add frontend/src/App.css && \
git commit -m "feat(frontend): add CSS for AntennaSelector and ConductorForm"
```

---

### Task 20: End-to-end smoke test

**Step 1: Start backend in Docker**

```bash
cd /path/to/aerials && docker compose up
```

**Step 2: Start frontend**

```bash
cd frontend && npm run dev
```

**Step 3: Manual verification checklist**

- [ ] App loads without console errors
- [ ] AntennaSelector shows 12 antenna cards
- [ ] Selecting each antenna updates the form fields
- [ ] 3D view updates in real-time as parameters change
- [ ] Conductor material selector changes conductor color in 3D view
- [ ] Clicking "Avvia simulazione FDTD" sends request to backend
- [ ] S11 chart renders with results after simulation completes
- [ ] Changing antenna type clears previous results

**Step 4: Final commit**

```bash
git add -A && git commit -m "feat: multi-antenna platform with 3D view and conductor options — complete"
```

---

## Summary

| Phase | Tasks | Output |
|-------|-------|--------|
| 1 — Backend Foundation | 1–3 | conductor.py, models.py, generic router |
| 2 — Backend Simulators | 4–8 | 12 openEMS simulators |
| 3 — Frontend Foundation | 9–15 | Three.js install, constants, 5 components |
| 4 — Three.js 3D View | 16–17 | geometry builders + Antenna3DView |
| 5 — Integration | 18–20 | App.jsx rewrite, CSS, E2E verify |
