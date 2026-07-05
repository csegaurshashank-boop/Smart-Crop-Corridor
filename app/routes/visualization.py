from fastapi import APIRouter, Depends
from app.services.corridor_service import get_corridors_by_field
from app.utils.geojson_builder import corridors_to_heatmap
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/visualization", tags=["Visualization"])


@router.get("/ndvi/{field_id}", summary="Get NDVI heatmap data for a field")
async def get_ndvi_heatmap(field_id: str, current_user: dict = Depends(get_current_user)):
    corridors = await get_corridors_by_field(field_id)
    return {
        "field_id": field_id,
        "total_corridors": len(corridors),
        "heatmap": corridors_to_heatmap(corridors),
    }