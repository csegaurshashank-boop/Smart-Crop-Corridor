from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RecommendationResponse(BaseModel):
    id: str
    farmer_id: str
    field_id: str
    corridor_id: str
    suggestions: List[str]
    predicted_crop: Optional[str]
    expected_yield: Optional[str]
    created_at: datetime


class CropPredictionRequest(BaseModel):
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    rainfall: float
    ndvi: float