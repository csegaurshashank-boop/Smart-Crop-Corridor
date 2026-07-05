from bson import ObjectId
from datetime import datetime
from app.database import get_db
from app.models.corridor import CorridorModel
from app.utils.grid_generator import generate_grid_corridors
from typing import List, Optional


async def create_corridors_for_field(
    field_id: str, lat: float, lng: float, area: float, grid_size: int = 5
):
    db = get_db()
    corridors = generate_grid_corridors(field_id, lat, lng, area, grid_size)
    docs = [CorridorModel.document(**c) for c in corridors]
    await db[CorridorModel.collection].insert_many(docs)


async def get_corridors_by_field(field_id: str) -> List[dict]:
    db = get_db()
    corridors = await db[CorridorModel.collection].find(
        {"field_id": field_id}
    ).to_list(length=500)
    return [_serialize(c) for c in corridors]


async def update_corridor_ndvi(
    corridor_id: str,
    ndvi: float,
    temperature: Optional[float] = None,
    soil_moisture: Optional[float] = None,
) -> dict:
    db = get_db()
    health_status = classify_health(ndvi)
    risk_level = classify_risk(ndvi, temperature, soil_moisture)

    update = {
        "ndvi": ndvi,
        "health_status": health_status,
        "risk_level": risk_level,
        "updated_at": datetime.utcnow(),
    }
    await db[CorridorModel.collection].update_one(
        {"_id": ObjectId(corridor_id)}, {"$set": update}
    )
    update["updated_at"] = update["updated_at"].isoformat()
    return {"corridor_id": corridor_id, **update}


def classify_health(ndvi: float) -> str:
    if ndvi > 0.6:
        return "healthy"
    elif ndvi >= 0.3:
        return "moderate"
    else:
        return "stress"


def classify_risk(ndvi: float, temp: Optional[float], moisture: Optional[float]) -> str:
    risks = []
    if ndvi < 0.3:
        risks.append("crop_stress")
    if temp and temp > 38:
        risks.append("heat_stress")
    if moisture and moisture < 20:
        risks.append("drought_risk")
    return risks[0] if risks else "low"


def _serialize(c: dict) -> dict:
    c["id"] = str(c.pop("_id"))
    if "updated_at" in c and hasattr(c["updated_at"], "isoformat"):
        c["updated_at"] = c["updated_at"].isoformat()
    return c