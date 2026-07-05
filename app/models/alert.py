from datetime import datetime


class AlertModel:
    collection = "alerts"

    @staticmethod
    def document(
        farmer_id: str,
        field_id: str,
        corridor: str,
        alert_type: str,
        message: str,
    ) -> dict:
        return {
            "farmer_id": farmer_id,
            "field_id": field_id,
            "corridor": corridor,
            "alert_type": alert_type,
            "message": message,
            "is_read": False,
            "created_at": datetime.utcnow(),
        }