from datetime import datetime
from typing import Optional


class AnalysisModel:
    collection = "analysis"

    @staticmethod
    def document(
        field_id: str,
        corridor_id: str,
        ndvi: float,
        health_status: str,
        temperature: Optional[float] = None,
        soil_moisture: Optional[float] = None,
    ) -> dict:
        return {
            "field_id": field_id,
            "corridor_id": corridor_id,
            "ndvi": ndvi,
            "health_status": health_status,
            "temperature": temperature,
            "soil_moisture": soil_moisture,
            "analyzed_at": datetime.utcnow(),
        }