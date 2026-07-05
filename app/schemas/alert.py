from pydantic import BaseModel
from datetime import datetime


class AlertResponse(BaseModel):
    id: str
    farmer_id: str
    field_id: str
    corridor: str
    alert_type: str
    message: str
    is_read: bool
    created_at: datetime