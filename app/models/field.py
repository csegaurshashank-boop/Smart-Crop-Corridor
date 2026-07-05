from datetime import datetime
from typing import Optional


class FieldModel:
    collection = "fields"

    @staticmethod
    def document(
        farmer_id: str,
        lat: float,
        lng: float,
        area: float,
        registered_by: str,
        boundary: Optional[dict] = None,
    ) -> dict:
        return {
            "farmer_id": farmer_id,
            "location": {"lat": lat, "lng": lng},
            "area": area,
            "registered_by": registered_by,
            "boundary": boundary,
            "analysis_status": "pending",
            "soil_type": None,
            "season": None,
            "recommended_crop": None,
            "crop_confidence": None,
            "alternative_crops": [],
            "recommendation_reason": None,
            "land_analysis": None,
            "created_at": datetime.utcnow(),
        }