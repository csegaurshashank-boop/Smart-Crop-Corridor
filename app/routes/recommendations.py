from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from app.schemas.recommendation import CropPredictionRequest  # type: ignore
from app.ml.prediction_service import predict_crop  # type: ignore
from app.services.recommendation_service import get_recommendations_by_field, predict_crop_from_data  # type: ignore
from app.services.data_aggregation_service import collect_field_data  # type: ignore
from app.services.farming_guide_service import get_farming_guide  # type: ignore
from app.services.field_service import get_field_by_id  # type: ignore
from app.services.season_service import validate_sowing_window  # type: ignore
from app.services.translation_service import translate_response, translate_crop_name  # type: ignore
from app.core.dependencies import get_current_user  # type: ignore

router = APIRouter(prefix="/recommendations", tags=["Recommendations & ML"])


@router.post("/predict-crop", summary="Predict best crop using ML model")
async def predict(
    payload: CropPredictionRequest,
    current_user: dict = Depends(get_current_user),
):
    return predict_crop(
        N=payload.N,
        P=payload.P,
        K=payload.K,
        temperature=payload.temperature,
        humidity=payload.humidity,
        rainfall=payload.rainfall,
        ndvi=payload.ndvi,
    )


@router.get("/field/{field_id}/summary", summary="AI pipeline summary for a field")
async def get_recommendation_summary(
    field_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    AI Pipeline endpoint:
    NDVI (corridors/Sentinel) → Weather (Open-Meteo) → Soil (SoilGrids) → ML Model

    Returns:
    {
        "crop": "Maize",
        "confidence": 82.0,
        "alternatives": ["Soybean", "Cotton"],
        "reason": "Based on soil NPK, NDVI and weather",
        "explanation": "Recommendation based on soil nutrients, weather, and vegetation health",
        "data_sources": {...}
    }
    """
    # 1. Aggregate live data (Open-Meteo + SoilGrids + corridor NDVI)
    try:
        field_data = await collect_field_data(field_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Data aggregation failed: {exc}")

    # 2. Run ML model (with rule-based fallback)
    result = predict_crop_from_data(field_data)

    # 3. Build explanation from data source provenance
    sources = field_data.get("data_sources", {})
    source_parts = []
    if sources.get("weather") == "open-meteo":
        source_parts.append("live weather (Open-Meteo)")
    else:
        source_parts.append("simulated weather")
    if sources.get("soil") == "soilgrids":
        source_parts.append("live soil data (SoilGrids ISRIC)")
    else:
        source_parts.append("simulated soil nutrients")
    ndvi_src = "satellite NDVI (corridors)" if sources.get("ndvi") == "corridors_db" else "simulated NDVI"
    source_parts.append(ndvi_src)

    explanation = (
        f"Recommendation based on soil nutrients (N:{field_data['n']:.0f} P:{field_data['p']:.0f} K:{field_data['k']:.0f} kg/ha), "
        f"vegetation health (NDVI: {field_data['ndvi']:.3f}), "
        f"and weather conditions (Temp: {field_data['temperature']:.1f}°C, "
        f"Humidity: {field_data['humidity']:.0f}%, Rainfall: {field_data['rainfall']:.0f} mm). "
        f"Data sources: {', '.join(source_parts)}."
    )

    return {
        "crop":         result["recommended_crop"],
        "confidence":   result["confidence"],
        "alternatives": result["alternatives"],
        "reason":       "Based on soil NPK, NDVI and weather",
        "explanation":  explanation,
        "model_used":   result["model_used"],
        "ndvi":         field_data["ndvi"],
        "data_sources": sources,
    }


@router.get("/field/{field_id}", summary="Get recommendations for a field")
async def get_recommendations(
    field_id: str,
    lang: str = "en",
    current_user: dict = Depends(get_current_user),
):
    data = await get_recommendations_by_field(field_id)
    return translate_response(data, lang)


@router.get("/guide/{field_id}", summary="Get detailed farming guide for a field")
async def get_guide(
    field_id: str,
    lang: str = "en",
    current_user: dict = Depends(get_current_user),
):
    field = await get_field_by_id(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    crop      = field.get("recommended_crop")
    if not crop:
        raise HTTPException(status_code=400, detail="No crop recommended yet. Run analysis first.")

    season    = field.get("season")
    soil_type = field.get("soil_type")
    area      = field.get("area")

    # Validate sowing window
    sowing = validate_sowing_window(crop)

    # Build response
    response = {
        "field_id":              field_id,
        "recommended_crop":      translate_crop_name(crop, lang),
        "crop_confidence":       field.get("crop_confidence"),
        "recommendation_reason": field.get("recommendation_reason"),
        "analysis_status":       field.get("analysis_status"),
        # sowing status
        "sowing_allowed":        sowing["sowing_allowed"],
        "sowing_window":         sowing["sowing_window"],
        "sowing_warning":        sowing.get("warning"),
        "sowing_reason":         sowing["reason"],
        "next_sowing_window":    sowing.get("next_sowing_window"),
        "alternative_crops":     sowing.get("alternative_crops", []),
        "current_month":         sowing["current_month"],
        "current_month_name":    sowing["current_month_name"],
    }

    if sowing["sowing_allowed"]:
        # Full farming guide (already in correct language)
        guide = get_farming_guide(crop, season, soil_type, area, lang=lang)
        response.update(guide)
    else:
        # Only planning guidance — no full cultivation steps
        crop_display = translate_crop_name(crop, lang)
        if lang == "hi":
            response["crop_name"]         = crop_display
            response["why_not_suitable"]  = sowing["warning"]
            response["planning_guidance"] = (
                f"अभी {crop_display} की खेती शुरू करना संभव नहीं है। "
                f"बुवाई का समय {sowing['sowing_window']} है। "
                f"आप {crop_display} को {sowing.get('next_sowing_window', 'अगले उपयुक्त समय')} में उगा सकते हैं। "
                f"आगामी मौसम के लिए भूमि तैयारी और बीज व्यवस्था पर ध्यान दें।"
            )
        else:
            response["crop_name"]         = crop.capitalize()
            response["why_not_suitable"]  = sowing["warning"]
            response["planning_guidance"] = (
                f"It is too late to start {crop.capitalize()} cultivation now. "
                f"The sowing window is {sowing['sowing_window']}. "
                f"You can grow {crop.capitalize()} in {sowing.get('next_sowing_window', 'the next suitable window')}. "
                f"Focus on preparing land and arranging inputs for the upcoming season."
            )

    # Translate the entire response (handles remaining dynamic text)
    return translate_response(response, lang)