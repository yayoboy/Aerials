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
    conductivity:      Optional[float]   = None
    cross_section:     CrossSection      = CrossSection.ROUND
    radius_mm:         Optional[float]   = 1.0
    outer_diameter_mm: Optional[float]   = None
    wall_thickness_mm: Optional[float]   = None
    width_mm:          Optional[float]   = None
    thickness_mm:      Optional[float]   = None

    @model_validator(mode='after')
    def check_cross_section_params(self):
        cs = self.cross_section
        if cs == CrossSection.ROUND and self.radius_mm is None:
            raise ValueError("radius_mm required for round cross-section")
        if cs == CrossSection.TUBE:
            if self.outer_diameter_mm is None or self.wall_thickness_mm is None:
                raise ValueError("outer_diameter_mm and wall_thickness_mm required for tube")
        if cs == CrossSection.FLAT:
            if self.width_mm is None or self.thickness_mm is None:
                raise ValueError("width_mm and thickness_mm required for flat cross-section")
        elif cs == CrossSection.SQUARE and self.width_mm is None:
            raise ValueError("width_mm required for square cross-section")
        return self

    def effective_radius_mm(self) -> float:
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
