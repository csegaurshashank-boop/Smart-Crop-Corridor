from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CorridorResponse(BaseModel):
    id: str
    field_id: str
    grid_position: str
    coordinates: List
    ndvi: float
    health_status: str
    risk_level: str
    updated_at: datetime


class NDVIUpdateRequest(BaseModel):
    corridor_id: str
    ndvi: float
    temperature: Optional[float] = None
    soil_moisture: Optional[float] = None