from datetime import datetime
from typing import List


class CorridorModel:
    collection = "corridors"

    @staticmethod
    def document(
        field_id: str,
        grid_position: str,
        coordinates: List,
        ndvi: float = 0.0,
        health_status: str = "unknown",
        risk_level: str = "unknown",
    ) -> dict:
        return {
            "field_id": field_id,
            "grid_position": grid_position,
            "coordinates": coordinates,
            "ndvi": ndvi,
            "health_status": health_status,
            "risk_level": risk_level,
            "updated_at": datetime.utcnow(),
        }