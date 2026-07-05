from datetime import datetime
from typing import List, Optional


class RecommendationModel:
    collection = "recommendations"

    @staticmethod
    def document(
        farmer_id: str,
        field_id: str,
        corridor_id: str,
        suggestions: List[str],
        predicted_crop: Optional[str] = None,
        expected_yield: Optional[str] = None,
    ) -> dict:
        return {
            "farmer_id": farmer_id,
            "field_id": field_id,
            "corridor_id": corridor_id,
            "suggestions": suggestions,
            "predicted_crop": predicted_crop,
            "expected_yield": expected_yield,
            "created_at": datetime.utcnow(),
        }