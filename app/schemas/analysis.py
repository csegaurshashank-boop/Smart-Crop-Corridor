from pydantic import BaseModel, field_validator
from typing import Optional


class AnalysisRequest(BaseModel):
    field_id: str
    corridor_id: str
    ndvi: float
    temperature: Optional[float] = None
    soil_moisture: Optional[float] = None

    @field_validator("ndvi")
    @classmethod
    def ndvi_range(cls, v: float) -> float:
        if not -1.0 <= v <= 1.0:
            raise ValueError("NDVI must be between -1.0 and 1.0")
        return v