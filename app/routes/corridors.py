from fastapi import APIRouter, Depends  # type: ignore
from app.schemas.corridor import NDVIUpdateRequest  # type: ignore
from app.services.corridor_service import get_corridors_by_field, update_corridor_ndvi  # type: ignore
from app.core.dependencies import get_current_user, require_role  # type: ignore

router = APIRouter(prefix="/corridors", tags=["Corridors"])


@router.get("/field/{field_id}", summary="Get all corridors for a field")
async def get_corridors(
    field_id: str,
    current_user: dict = Depends(get_current_user)
):
    corridors = await get_corridors_by_field(field_id)
    return {"field_id": field_id, "total": len(corridors), "corridors": corridors}


@router.put("/update-ndvi", summary="Update NDVI for a corridor")
async def update_ndvi(
    payload: NDVIUpdateRequest,
    current_user: dict = Depends(require_role("manager", "admin", "super_admin")),
):
    updated = await update_corridor_ndvi(
        payload.corridor_id,
        payload.ndvi,
        payload.temperature,
        payload.soil_moisture,
    )
    return updated