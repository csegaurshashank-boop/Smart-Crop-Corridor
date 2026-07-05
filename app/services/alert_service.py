from bson import ObjectId  # type: ignore[import-untyped]
from app.database import get_db  # type: ignore
from app.models.alert import AlertModel  # type: ignore
from app.services.risk_service import detect_risks  # type: ignore
from typing import List, Optional


async def create_alert(
    farmer_id: str,
    field_id: str,
    corridor: str,
    alert_type: str,
    message: str,
) -> dict:
    db = get_db()
    doc = AlertModel.document(
        farmer_id=farmer_id,
        field_id=field_id,
        corridor=corridor,
        alert_type=alert_type,
        message=message,
    )
    result = await db[AlertModel.collection].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc


async def generate_alerts_for_corridor(
    farmer_id: str,
    field_id: str,
    corridor_id: str,
    grid_position: str,
    ndvi: float,
    temperature: Optional[float] = None,
    soil_moisture: Optional[float] = None,
) -> List[dict]:
    risks = detect_risks(ndvi, temperature, soil_moisture)
    created = []
    for risk in risks:
        alert = await create_alert(
            farmer_id=farmer_id,
            field_id=field_id,
            corridor=grid_position,
            alert_type=risk["risk_id"],
            message=risk["message"],
        )
        created.append(alert)
    return created


async def get_alerts_for_farmer(farmer_id: str) -> List[dict]:
    db = get_db()
    alerts = (
        await db[AlertModel.collection]
        .find({"farmer_id": farmer_id})
        .sort("created_at", -1)
        .to_list(length=200)
    )
    return [_serialize(a) for a in alerts]


async def mark_alert_read(alert_id: str) -> None:
    db = get_db()
    await db[AlertModel.collection].update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"is_read": True}},
    )


def _serialize(a: dict) -> dict:
    a = dict(a)
    a["id"] = str(a.pop("_id"))
    return a