from pydantic import BaseModel, field_validator
from typing import Optional, List


class BoundaryCoordinates(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class FieldCreate(BaseModel):
    farmer_id: str
    lat: float
    lng: float
    area: float
    boundary: Optional[BoundaryCoordinates] = None

    @field_validator("area")
    @classmethod
    def area_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Area must be greater than 0")
        return round(v, 4)


class FieldResponse(BaseModel):
    id: str
    farmer_id: str
    lat: float
    lng: float
    area: float
    analysis_status: str
    recommended_crop: Optional[str] = None
    crop_confidence: Optional[float] = None
    alternative_crops: List[str] = []