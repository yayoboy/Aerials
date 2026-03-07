import pytest
from app.models import (
    DipoleParams, MonopoleParams, YagiParams, PatchParams, SimulationRequest
)
from app.conductor import ConductorParams

def test_dipole_defaults():
    p = DipoleParams()
    assert p.frequency_mhz == 300.0
    assert p.length_mm == 475.0

def test_yagi_has_directors():
    p = YagiParams()
    assert len(p.director_lengths_mm) >= 1

def test_simulation_request_has_conductor():
    req = SimulationRequest(antenna_type="dipole",
                            antenna_params={"frequency_mhz": 300})
    assert req.conductor.material == "copper"

def test_patch_has_substrate_fields():
    p = PatchParams()
    assert p.substrate_er == 4.4
    assert p.substrate_height_mm == 1.6
