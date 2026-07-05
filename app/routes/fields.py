from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import Optional
from app.services.field_service import (  # type: ignore
    register_field,
    get_all_fields,
    get_fields_by_farmer,
    get_field_by_id,
    trigger_analysis,
    delete_field_by_id,
)
from app.services.translation_service import translate_response, translate_crop_name  # type: ignore
from app.core.dependencies import require_role, get_current_user  # type: ignore

router = APIRouter(prefix="/fields", tags=["Fields"])


class FieldCreate(BaseModel):
    farmer_id: str
    lat: float
    lng: float
    area: float
    boundary: Optional[dict] = None


@router.post("/register", summary="Manager registers a farmer's field")
async def register(
    field: FieldCreate,
    current_user: dict = Depends(require_role("manager", "admin", "super_admin")),
):
    return await register_field(
        farmer_id=field.farmer_id,
        lat=field.lat,
        lng=field.lng,
        area=field.area,
        registered_by=current_user["user_id"],
        boundary=field.boundary,
    )


@router.get("/list", summary="List all fields")
async def get_fields(
    farmer_id: Optional[str] = None,
    lang: str = "en",
    current_user: dict = Depends(get_current_user),
):
    # Farmers can only see their own fields
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    if farmer_id:
        fields = await get_fields_by_farmer(farmer_id)
    else:
        fields = await get_all_fields()
    return translate_response(fields, lang)


@router.get("/{field_id}", summary="Get a specific field by ID")
async def get_field(
    field_id: str,
    lang: str = "en",
    current_user: dict = Depends(get_current_user),
):
    field = await get_field_by_id(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return translate_response(field, lang)


@router.post("/analyze/{field_id}", summary="Re-trigger AI analysis for a field")
async def analyze_field(
    field_id: str,
    current_user: dict = Depends(require_role("manager", "admin", "super_admin")),
):
    await trigger_analysis(field_id)
    return {"message": "Analysis re-triggered", "field_id": field_id}


@router.delete("/{field_id}", summary="Delete a field and all its data")
async def delete_field(
    field_id: str,
    current_user: dict = Depends(require_role("manager", "admin", "super_admin")),
):
    deleted = await delete_field_by_id(field_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Field not found")
    return {"message": "Field deleted successfully", "field_id": field_id}