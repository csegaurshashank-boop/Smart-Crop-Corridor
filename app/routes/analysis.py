from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.services import field_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/status/{field_id}")
async def get_analysis_status(field_id: str, current_user=Depends(get_current_user)):
    """
    Poll this endpoint every 2-3 seconds from the frontend.
    Returns analysis_status + full results when completed.
    """
    db = get_db()
    field = await db["fields"].find_one({"_id": ObjectId(field_id)})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return {
        "field_id": field_id,
        "analysis_status": field.get("analysis_status", "pending"),
        "recommended_crop": field.get("recommended_crop"),
        "crop_confidence": field.get("crop_confidence"),
        "alternative_crops": field.get("alternative_crops", []),
        "land_analysis": field.get("land_analysis"),
        "model_metrics": field.get("model_metrics"),
    }


@router.post("/run-field/{field_id}")
async def run_analysis(
    field_id: str,
    current_user=Depends(require_role("manager", "admin", "super_admin")),
):
    await field_service.trigger_analysis(field_id)
    return {"message": "Analysis triggered", "field_id": field_id}


@router.get("/field/{field_id}")
async def get_analysis_history(field_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    field = await db["fields"].find_one({"_id": ObjectId(field_id)})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    corridors = await db["corridors"].find({"field_id": field_id}).to_list(length=25)
    for c in corridors:
        c["id"] = str(c.pop("_id"))

    return {
        "field_id": field_id,
        "analysis_status": field.get("analysis_status"),
        "land_analysis": field.get("land_analysis"),
        "recommended_crop": field.get("recommended_crop"),
        "crop_confidence": field.get("crop_confidence"),
        "alternative_crops": field.get("alternative_crops", []),
        "model_metrics": field.get("model_metrics"),
        "corridors": corridors,
    }