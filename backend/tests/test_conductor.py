import pytest
from app.conductor import ConductorMaterial, CrossSection, ConductorParams, get_conductivity

def test_known_material_conductivity():
    assert get_conductivity(ConductorMaterial.COPPER) == pytest.approx(5.8e7)

def test_custom_material_requires_value():
    # Happy path: custom with value is accepted
    p = ConductorParams(material=ConductorMaterial.CUSTOM, conductivity=1e6,
                        cross_section=CrossSection.ROUND, radius_mm=1.0)
    assert p.conductivity == 1e6
    # Must raise when no conductivity provided to get_conductivity
    with pytest.raises(ValueError):
        get_conductivity(ConductorMaterial.CUSTOM)

def test_round_section_requires_radius():
    with pytest.raises(Exception):
        ConductorParams(material=ConductorMaterial.COPPER,
                        cross_section=CrossSection.ROUND, radius_mm=None)

def test_tube_section_requires_outer_and_wall():
    p = ConductorParams(material=ConductorMaterial.ALUMINUM,
                        cross_section=CrossSection.TUBE,
                        outer_diameter_mm=10.0, wall_thickness_mm=1.0)
    assert p.outer_diameter_mm == 10.0

def test_square_section_requires_width():
    with pytest.raises(Exception):
        ConductorParams(cross_section=CrossSection.SQUARE, width_mm=None)

def test_flat_section_requires_width_and_thickness():
    with pytest.raises(Exception):
        ConductorParams(cross_section=CrossSection.FLAT, width_mm=10.0)  # no thickness_mm

def test_effective_radius_tube():
    p = ConductorParams(cross_section=CrossSection.TUBE,
                        outer_diameter_mm=10.0, wall_thickness_mm=1.0)
    assert p.effective_radius_mm() == pytest.approx(5.0)

def test_effective_radius_flat():
    p = ConductorParams(cross_section=CrossSection.FLAT, width_mm=4.0, thickness_mm=1.0)
    import math
    assert p.effective_radius_mm() == pytest.approx(math.sqrt(4.0) / 2.0)
