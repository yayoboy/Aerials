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
                        cross_section=CrossSection.ROUND, radius_mm=None)

def test_tube_section_requires_outer_and_wall():
    p = ConductorParams(material=ConductorMaterial.ALUMINUM,
                        cross_section=CrossSection.TUBE,
                        outer_diameter_mm=10.0, wall_thickness_mm=1.0)
    assert p.outer_diameter_mm == 10.0
