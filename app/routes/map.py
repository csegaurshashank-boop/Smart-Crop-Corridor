from fastapi import APIRouter, Depends
from app.services.corridor_service import get_corridors_by_field
from app.utils.geojson_builder import corridors_to_geojson
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/map", tags=["Map & GeoJSON"])


@router.get("/geojson/{field_id}", summary="Get corridors as GeoJSON FeatureCollection")
async def get_geojson(field_id: str, current_user: dict = Depends(get_current_user)):
    corridors = await get_corridors_by_field(field_id)
    return corridors_to_geojson(corridors)