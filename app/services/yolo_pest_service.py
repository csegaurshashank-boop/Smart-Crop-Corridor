"""
app/services/yolo_pest_service.py

YOLO-based Crop Pest & Disease Detection Service
Using Ultralytics YOLOv8 / YOLO11 architecture.

MODEL FILE:
  Place your trained weights at:
    app/ml/crop_disease.pt

  Free pre-trained options:
    • PlantDoc YOLO  → https://github.com/pratikkayal/PlantDoc-Dataset
    • Roboflow Plant Disease datasets (export as YOLOv8)
    • Train your own via: python app/ml/train_yolo.py

FALLBACK:
  If model file is missing or ultralytics is not installed,
  the system automatically falls back to the hash-seeded
  simulation — the API NEVER crashes.

CLASS MAP:
  Edit DISEASE_MAP below to match your model's class indices.
  Default map covers 38 PlantVillage classes.
"""

from __future__ import annotations

import hashlib
import io
import os
import random
from pathlib import Path
from typing import Optional

# ── Model path ────────────────────────────────────────────────────────────────
_MODEL_PATH = Path(__file__).parent.parent / "ml" / "crop_disease.pt"

# ── Cached model (loaded once on first call) ──────────────────────────────────
_model = None
_model_load_attempted = False


# ── PlantVillage 38-class disease map ────────────────────────────────────────
# Keys = class index returned by YOLO model
# Adjust to match your model's actual class list
DISEASE_MAP: dict[int, dict] = {
    0:  {"disease": "Apple Scab",                "severity": "high",     "recommendation": "Apply Captan 50% WP at 2 g/L. Remove fallen leaves. Spray at 7-day intervals during wet weather."},
    1:  {"disease": "Apple Black Rot",            "severity": "high",     "recommendation": "Apply Myclobutanil at 1 mL/L. Prune infected branches. Destroy mummified fruit."},
    2:  {"disease": "Apple Cedar Rust",           "severity": "moderate", "recommendation": "Apply Propiconazole 25% EC at 1 mL/L. Remove nearby juniper hosts if possible."},
    3:  {"disease": "Apple Healthy",              "severity": "low",      "recommendation": "No disease detected. Continue regular monitoring and balanced nutrition."},
    4:  {"disease": "Blueberry Healthy",          "severity": "low",      "recommendation": "Crop appears healthy. Maintain soil pH 4.5–5.5 for optimal growth."},
    5:  {"disease": "Cherry Powdery Mildew",      "severity": "moderate", "recommendation": "Apply Sulphur 80% WP at 2 g/L. Improve air circulation. Avoid excess nitrogen."},
    6:  {"disease": "Cherry Healthy",             "severity": "low",      "recommendation": "Healthy cherry crop. Monitor for leaf curl and fruit fly during season."},
    7:  {"disease": "Corn Grey Leaf Spot",        "severity": "high",     "recommendation": "Apply Azoxystrobin 23% SC at 1 mL/L. Plant resistant hybrids next season."},
    8:  {"disease": "Corn Common Rust",           "severity": "moderate", "recommendation": "Apply Mancozeb 75% WP at 2.5 g/L at first sign. Use rust-resistant varieties."},
    9:  {"disease": "Corn Northern Leaf Blight",  "severity": "high",     "recommendation": "Apply Propiconazole 25% EC at 1 mL/L. Improve crop rotation. Remove residue post-harvest."},
    10: {"disease": "Corn Healthy",               "severity": "low",      "recommendation": "Corn is healthy. Ensure adequate potassium and phosphorus for grain fill."},
    11: {"disease": "Grape Black Rot",            "severity": "high",     "recommendation": "Apply Myclobutanil 10% WP at 1 g/L. Remove mummified berries. Spray at bloom."},
    12: {"disease": "Grape Black Measles",        "severity": "high",     "recommendation": "Apply Thiophanate-methyl 70% WP at 1 g/L. Trunk surgery may be required for older vines."},
    13: {"disease": "Grape Leaf Blight",          "severity": "moderate", "recommendation": "Apply Copper oxychloride 50% WP at 3 g/L. Avoid overhead irrigation."},
    14: {"disease": "Grape Healthy",              "severity": "low",      "recommendation": "Healthy vines. Maintain proper canopy management for air flow."},
    15: {"disease": "Orange Haunglongbing (HLB)", "severity": "high",     "recommendation": "No cure available. Remove infected trees immediately. Control Asian citrus psyllid vector with Imidacloprid."},
    16: {"disease": "Peach Bacterial Spot",       "severity": "moderate", "recommendation": "Apply Copper hydroxide 77% WP at 3 g/L. Prune during dry weather. Avoid wounds."},
    17: {"disease": "Peach Healthy",              "severity": "low",      "recommendation": "Peach is healthy. Thin fruit for larger size and disease prevention."},
    18: {"disease": "Pepper Bacterial Spot",      "severity": "moderate", "recommendation": "Apply Streptomycin sulphate + Copper at 1 g/L each. Use certified seed."},
    19: {"disease": "Pepper Healthy",             "severity": "low",      "recommendation": "Healthy pepper crop. Monitor for aphids and thrips regularly."},
    20: {"disease": "Potato Early Blight",        "severity": "moderate", "recommendation": "Apply Chlorothalonil 75% WP at 2 g/L. Destroy infected foliage. Maintain nutrition."},
    21: {"disease": "Potato Late Blight",         "severity": "high",     "recommendation": "Apply Metalaxyl + Mancozeb WP at 2.5 g/L IMMEDIATELY. Late blight spreads rapidly in cool wet weather."},
    22: {"disease": "Potato Healthy",             "severity": "low",      "recommendation": "Potato crop looks healthy. Apply earthing-up to prevent greening."},
    23: {"disease": "Raspberry Healthy",          "severity": "low",      "recommendation": "Healthy canes. Prune old canes after harvest for next season yield."},
    24: {"disease": "Soybean Healthy",            "severity": "low",      "recommendation": "Soybean is healthy. Monitor for soybean mosaic virus and stem canker during reproductive stages."},
    25: {"disease": "Squash Powdery Mildew",      "severity": "moderate", "recommendation": "Apply Sulphur 80% WP at 2 g/L or Neem oil 5 mL/L. Avoid wetting leaves."},
    26: {"disease": "Strawberry Leaf Scorch",     "severity": "moderate", "recommendation": "Apply Captan 50% WP at 2 g/L. Remove old leaves. Ensure good drainage."},
    27: {"disease": "Strawberry Healthy",         "severity": "low",      "recommendation": "Healthy strawberry. Apply mulch to retain moisture and prevent splash infection."},
    28: {"disease": "Tomato Bacterial Spot",      "severity": "moderate", "recommendation": "Apply Copper oxychloride + Streptomycin. Use drip irrigation. Rotate crops."},
    29: {"disease": "Tomato Early Blight",        "severity": "moderate", "recommendation": "Apply Chlorothalonil 75% WP at 2 g/L. Remove lower infected leaves. Stake plants."},
    30: {"disease": "Tomato Late Blight",         "severity": "high",     "recommendation": "Apply Metalaxyl + Mancozeb at 2.5 g/L URGENTLY. Remove infected plants. Do not compost."},
    31: {"disease": "Tomato Leaf Mold",           "severity": "moderate", "recommendation": "Apply Mancozeb 75% WP at 2.5 g/L. Improve greenhouse ventilation. Reduce humidity."},
    32: {"disease": "Tomato Septoria Leaf Spot",  "severity": "moderate", "recommendation": "Apply Chlorothalonil at 2 g/L. Remove and destroy infected leaves promptly."},
    33: {"disease": "Tomato Spider Mites",        "severity": "moderate", "recommendation": "Apply Abamectin 1.8% EC at 0.5 mL/L or Neem oil. Increase humidity — mites thrive in dry conditions."},
    34: {"disease": "Tomato Target Spot",         "severity": "moderate", "recommendation": "Apply Azoxystrobin 23% SC at 1 mL/L. Avoid leaf wetness. Improve air circulation."},
    35: {"disease": "Tomato Yellow Leaf Curl Virus", "severity": "high",  "recommendation": "No direct cure. Remove infected plants. Control whitefly vector with Thiamethoxam 25% WG."},
    36: {"disease": "Tomato Mosaic Virus",        "severity": "high",     "recommendation": "No cure. Remove infected plants. Disinfect tools. Control aphid vectors."},
    37: {"disease": "Tomato Healthy",             "severity": "low",      "recommendation": "Tomato crop is healthy. Maintain consistent watering and stake for support."},
}

# ── Treatments lookup (by severity + disease keywords) ───────────────────────
_TREATMENTS = {
    "Blight":         ["Mancozeb 75% WP (2.5 g/L)", "Chlorothalonil 75% WP (2 g/L)"],
    "Rust":           ["Propiconazole 25% EC (1 mL/L)", "Tebuconazole 25.9% EC (1 mL/L)"],
    "Powdery Mildew": ["Sulphur 80% WP (2 g/L)", "Hexaconazole 5% EC (1 mL/L)"],
    "Spot":           ["Copper oxychloride 50% WP (3 g/L)", "Streptomycin 90% SP (0.5 g/L)"],
    "Rot":            ["Captan 50% WP (2 g/L)", "Myclobutanil 10% WP (1 g/L)"],
    "Virus":          ["Remove infected plants", "Control insect vectors with Imidacloprid"],
    "Mites":          ["Abamectin 1.8% EC (0.5 mL/L)", "Neem oil 5 mL/L organic spray"],
    "Healthy":        [],
}


def _get_treatments(disease_name: str) -> list[str]:
    for keyword, treatments in _TREATMENTS.items():
        if keyword in disease_name:
            return treatments
    return ["Consult local agronomist for specific treatment protocol."]


def _get_prevention(disease_name: str) -> str:
    if "Healthy" in disease_name:
        return "Maintain current crop management practices. Monitor weekly."
    if "Virus" in disease_name:
        return "Use certified virus-free planting material. Control insect vectors early in the season."
    if "Blight" in disease_name or "Rot" in disease_name:
        return "Use disease-resistant varieties. Rotate crops annually. Avoid overhead irrigation."
    if "Mildew" in disease_name:
        return "Plant in well-ventilated areas. Avoid excess nitrogen. Use resistant cultivars."
    return "Practice crop rotation, use certified seeds, and maintain balanced fertilisation."


# ── Model loader (lazy, cached) ───────────────────────────────────────────────

def _load_model():
    """
    Attempt to load YOLO model once.
    Returns model object or None if unavailable.
    """
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True

    if not _MODEL_PATH.exists():
        print(f"[yolo_pest] Model not found at {_MODEL_PATH} — using simulation fallback.")
        return None

    try:
        from ultralytics import YOLO  # type: ignore
        _model = YOLO(str(_MODEL_PATH))
        print(f"[yolo_pest] ✅ YOLO model loaded from {_MODEL_PATH}")
        return _model
    except ImportError:
        print("[yolo_pest] ultralytics not installed — using simulation fallback.")
        return None
    except Exception as exc:
        print(f"[yolo_pest] Model load failed: {exc} — using simulation fallback.")
        return None


# ── YOLO inference ────────────────────────────────────────────────────────────

def _run_yolo(image_bytes: bytes) -> Optional[dict]:
    """
    Run YOLO inference on image bytes.
    Returns detection dict or None if model unavailable / inference fails.
    """
    model = _load_model()
    if model is None:
        return None

    try:
        from PIL import Image as PILImage  # type: ignore
        img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        results = model(img, verbose=False)

        if not results or len(results) == 0:
            return None

        # Pick highest-confidence detection
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            # No box detected → assume healthy (class 37 equivalent fallback)
            return {
                "disease":    "Healthy Crop",
                "severity":   "low",
                "confidence": 72.0,
            }

        # boxes.conf → confidence scores, boxes.cls → class indices
        import torch  # type: ignore
        confs   = boxes.conf.cpu()
        classes = boxes.cls.cpu().long()

        best_idx  = int(torch.argmax(confs).item())
        best_cls  = int(classes[best_idx].item())
        best_conf = round(float(confs[best_idx].item()) * 100, 1)

        info = DISEASE_MAP.get(best_cls)
        if info is None:
            print(f"[yolo_pest] Unknown class {best_cls} — falling back to simulation.")
            return None

        return {
            "disease":    info["disease"],
            "severity":   info["severity"],
            "confidence": min(97.0, max(40.0, best_conf)),
        }

    except Exception as exc:
        print(f"[yolo_pest] Inference error: {exc}")
        return None


# ── Simulation fallback ───────────────────────────────────────────────────────

_SIM_DISEASES = [
    {"disease": "Leaf Blight",         "severity": "high"},
    {"disease": "Powdery Mildew",      "severity": "moderate"},
    {"disease": "Aphid Infestation",   "severity": "moderate"},
    {"disease": "Bacterial Leaf Spot", "severity": "high"},
    {"disease": "Rust Disease",        "severity": "high"},
    {"disease": "Whitefly Damage",     "severity": "low"},
    {"disease": "Downy Mildew",        "severity": "moderate"},
    {"disease": "Healthy Crop",        "severity": "low"},
]
_SIM_WEIGHTS = [2, 3, 3, 2, 2, 3, 2, 5]


def _run_simulation(image_bytes: bytes) -> dict:
    """Hash-seeded simulation — deterministic per image, realistic output."""
    digest = hashlib.sha256(image_bytes).hexdigest()
    seed   = int(digest[:8], 16)
    rng    = random.Random(seed)

    picked   = rng.choices(_SIM_DISEASES, weights=_SIM_WEIGHTS, k=1)[0]
    conf_ranges = {"low": (70, 86), "moderate": (76, 90), "high": (82, 95)}
    lo, hi   = conf_ranges[picked["severity"]]
    confidence = round(rng.uniform(lo, hi), 1)

    return {
        "disease":    picked["disease"],
        "severity":   picked["severity"],
        "confidence": confidence,
    }


# ── Public interface ──────────────────────────────────────────────────────────

def detect_disease(image_bytes: bytes) -> dict:
    """
    Main entry point for pest/disease detection.

    Priority:
      1. YOLO model (real AI inference) if app/ml/crop_disease.pt exists
      2. Hash-seeded simulation fallback (always works)

    Returns:
    {
        "disease":        str,
        "confidence":     float,
        "severity":       "low" | "moderate" | "high",
        "recommendation": str,
        "treatments":     list[str],
        "prevention":     str,
        "model_used":     "yolo" | "simulation"
    }
    """
    # Try YOLO first
    yolo_result = _run_yolo(image_bytes)
    if yolo_result:
        disease    = yolo_result["disease"]
        severity   = yolo_result["severity"]
        confidence = yolo_result["confidence"]
        model_used = "yolo"
    else:
        # Fallback simulation
        sim        = _run_simulation(image_bytes)
        disease    = sim["disease"]
        severity   = sim["severity"]
        confidence = sim["confidence"]
        model_used = "simulation"

    # Build full recommendation
    # Try DISEASE_MAP first (for YOLO classes), else use keyword lookup
    disease_info = next(
        (v for v in DISEASE_MAP.values() if v["disease"] == disease), None
    )
    recommendation = (
        disease_info["recommendation"]
        if disease_info
        else f"Consult an agronomist. Disease: {disease}"
    )

    return {
        "disease":        disease,
        "confidence":     confidence,
        "severity":       severity,
        "recommendation": recommendation,
        "treatments":     _get_treatments(disease),
        "prevention":     _get_prevention(disease),
        "model_used":     model_used,
    }
