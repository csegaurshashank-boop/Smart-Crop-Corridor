import asyncio
from datetime import datetime
from bson import ObjectId
from app.database import get_db
from app.models.field import FieldModel
from app.utils.grid_generator import generate_grid_corridors   # your existing util


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def register_field(farmer_id: str, lat: float, lng: float,
                         area: float, registered_by: str, boundary=None):
    db = get_db()

    # 1. build and insert field document
    doc = FieldModel.document(farmer_id, lat, lng, area, registered_by, boundary)
    result = await db["fields"].insert_one(doc)
    field_id = str(result.inserted_id)

    # 2. generate 25-corridor grid (reuse existing util)
    try:
        corridors = generate_grid_corridors(field_id, lat, lng, area)
        if corridors:
            await db["corridors"].insert_many(corridors)
    except Exception:
        pass  # grid generation failure should not block registration

    # 3. run AI analysis synchronously (ensures completion before returning)
    try:
        from app.services.land_analysis_service import run_land_analysis
        await db["fields"].update_one(
            {"_id": ObjectId(field_id)},
            {"$set": {"analysis_status": "running"}},
        )
        await run_land_analysis(field_id)
    except Exception as exc:
        await db["fields"].update_one(
            {"_id": ObjectId(field_id)},
            {"$set": {"analysis_status": "failed"}},
        )
        print(f"[field_service] analysis failed for {field_id}: {exc}")

    doc["_id"] = result.inserted_id
    return _serialize(doc)


async def _run_analysis_background(field_id: str):
    db = get_db()
    try:
        await db["fields"].update_one(
            {"_id": ObjectId(field_id)},
            {"$set": {"analysis_status": "running"}},
        )
        from app.services.land_analysis_service import run_land_analysis
        await run_land_analysis(field_id)
    except Exception as exc:
        await db["fields"].update_one(
            {"_id": ObjectId(field_id)},
            {"$set": {"analysis_status": "failed"}},
        )
        print(f"[field_service] analysis failed for {field_id}: {exc}")


async def get_fields_by_farmer(farmer_id: str):
    db = get_db()
    docs = await db["fields"].find({"farmer_id": farmer_id}).to_list(length=200)
    return [_serialize(d) for d in docs]


async def get_all_fields():
    db = get_db()
    docs = await db["fields"].find().to_list(length=500)
    return [_serialize(d) for d in docs]


async def get_field_by_id(field_id: str):
    db = get_db()
    doc = await db["fields"].find_one({"_id": ObjectId(field_id)})
    if not doc:
        return None
    return _serialize(doc)


async def trigger_analysis(field_id: str):
    """Manually re-trigger analysis (e.g. from /fields/analyze/{id})."""
    from app.services.land_analysis_service import run_land_analysis
    db = get_db()
    await db["fields"].update_one(
        {"_id": ObjectId(field_id)},
        {"$set": {"analysis_status": "running"}},
    )
    try:
        await run_land_analysis(field_id)
    except Exception as exc:
        await db["fields"].update_one(
            {"_id": ObjectId(field_id)},
            {"$set": {"analysis_status": "failed"}},
        )
        raise exc


async def delete_field_by_id(field_id: str) -> bool:
    """
    Delete a field and all its related data (corridors, recommendations, alerts).
    Returns True if the field existed and was deleted, False if not found.
    """
    db = get_db()
    result = await db["fields"].delete_one({"_id": ObjectId(field_id)})
    if result.deleted_count == 0:
        return False
    # Clean up related collections
    await db["corridors"].delete_many({"field_id": field_id})
    await db["recommendations"].delete_many({"field_id": field_id})
    await db["alerts"].delete_many({"field_id": field_id})
    print(f"[field_service] Field {field_id} and all related data deleted.")
    return True