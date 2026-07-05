"""
app/routes/pest_detection.py

Image-based Pest Detection Route
POST /pest-detection/analyze

Accepts an uploaded crop image (multipart/form-data),
runs YOLO inference via yolo_pest_service,
and returns structured pest/disease detection results.

YOLO pipeline:
  Model : app/ml/crop_disease.pt  (YOLOv8/YOLO11 .pt weights)
  Fallback: hash-seeded simulation if model file is absent
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.dependencies import get_current_user  # type: ignore
from app.services.yolo_pest_service import detect_disease  # type: ignore

router = APIRouter(prefix="/pest-detection", tags=["Pest Detection (Image AI)"])


@router.post("/analyze", summary="Detect pests/diseases from a crop image")
async def analyze_pest_image(
    image: UploadFile = File(..., description="Crop/leaf image — JPG, PNG, WEBP"),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a crop image for AI-powered pest and disease detection.

    Pipeline:
      Image → YOLO model (app/ml/crop_disease.pt) → result
      If model missing → simulation fallback (always returns valid data)

    Returns:
    {
        "disease": str,
        "confidence": float,
        "severity": "low" | "moderate" | "high",
        "recommendation": str,
        "treatments": list[str],
        "prevention": str,
        "model_used": "yolo" | "simulation"
    }
    """
    # ── Validate content type ─────────────────────────────────────────────────
    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file. Please upload a JPG, PNG, or WEBP image.",
        )

    # ── Read image (max 10 MB) ────────────────────────────────────────────────
    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image file received.")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Image too large. Maximum allowed size is 10 MB.",
        )

    # ── Run detection ─────────────────────────────────────────────────────────
    try:
        result = detect_disease(image_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Detection pipeline error: {exc}",
        )

    return result
