from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.conductor import ConductorParams

class DipoleParams(BaseModel):
    frequency_mhz: float = 300.0
    length_mm:     float = 475.0

class FoldedDipoleParams(BaseModel):
    frequency_mhz: float = 144.0
    length_mm:     float = 1020.0
    spacing_mm:    float = 25.0

class MonopoleParams(BaseModel):
    frequency_mhz:  float = 300.0
    length_mm:      float = 237.5
    groundplane_mm: float = 300.0

class YagiParams(BaseModel):
    frequency_mhz:       float       = 144.0
    driven_length_mm:    float       = 1020.0
    reflector_length_mm: float       = 1050.0
    director_lengths_mm: List[float] = [980.0, 960.0]
    element_spacing_mm:  float       = 300.0

class InvertedVParams(BaseModel):
    frequency_mhz:  float = 7.0
    length_mm:      float = 20200.0
    apex_angle_deg: float = 120.0
    height_mm:      float = 15000.0

class LoopParams(BaseModel):
    frequency_mhz: float = 14.0
    perimeter_mm:  float = 21400.0
    shape:         str   = "square"

class HelixParams(BaseModel):
    frequency_mhz: float = 2400.0
    diameter_mm:   float = 40.0
    pitch_mm:      float = 30.0
    turns:         int   = 8
    mode:          str   = "axial"

class SleeveParams(BaseModel):
    frequency_mhz:      float = 144.0
    monopole_length_mm: float = 490.0
    sleeve_length_mm:   float = 245.0

class DisconeParams(BaseModel):
    frequency_mhz:    float = 400.0
    cone_length_mm:   float = 185.0
    cone_angle_deg:   float = 60.0
    disc_diameter_mm: float = 150.0

class GroundPlaneParams(BaseModel):
    frequency_mhz:    float = 146.0
    radial_length_mm: float = 490.0
    num_radials:      int   = 4
    radial_angle_deg: float = 45.0

class JPoleParams(BaseModel):
    frequency_mhz:    float = 146.0
    long_element_mm:  float = 1000.0
    stub_length_mm:   float = 330.0
    stub_spacing_mm:  float = 25.0

class PatchParams(BaseModel):
    frequency_mhz:       float = 2400.0
    width_mm:            float = 38.0
    length_mm:           float = 29.0
    substrate_er:        float = 4.4
    substrate_height_mm: float = 1.6

class MoxonParams(BaseModel):
    frequency_mhz:     float = 144.0
    element_length_mm: float = 990.0
    tail_length_mm:    float = 171.0
    feed_gap_mm:       float = 27.0

class SimulationRequest(BaseModel):
    antenna_params:  Dict[str, Any]
    conductor:       ConductorParams = ConductorParams()
    with_radiation:  bool = False
