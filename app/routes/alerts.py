from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from app.services.alert_service import get_alerts_for_farmer, mark_alert_read  # type: ignore
from app.services.irrigation_service import generate_irrigation_alert  # type: ignore
from app.services.translation_service import translate_response  # type: ignore
from app.core.dependencies import get_current_user  # type: ignore

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/farmer/{farmer_id}", summary="Get all alerts for a farmer")
async def get_alerts(
    farmer_id: str,
    lang: str = "en",
    current_user: dict = Depends(get_current_user),
):
    # Farmers can only see their own alerts
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    alerts = await get_alerts_for_farmer(farmer_id)
    return translate_response(alerts, lang)


@router.patch("/{alert_id}/read", summary="Mark alert as read")
async def read_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    await mark_alert_read(alert_id)
    return {"message": "Alert marked as read"}


@router.get("/irrigation/{field_id}", summary="Get irrigation status for a field")
async def get_irrigation(
    field_id: str,
    lang: str = "en",
    current_user: dict = Depends(get_current_user),
):
    result = await generate_irrigation_alert(field_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return translate_response(result, lang)