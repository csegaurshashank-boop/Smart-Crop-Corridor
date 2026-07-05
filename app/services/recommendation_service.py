from bson import ObjectId
from app.database import get_db
from app.models.recommendation import RecommendationModel
from typing import List, Optional, Dict, Any

SUGGESTION_RULES = [
    {
        "condition": lambda ndvi, temp, moisture: ndvi is not None and ndvi < 0.3,
        "suggestions": [
            "Increase irrigation frequency",
            "Apply balanced NPK fertilizer",
            "Test soil pH and amend if needed",
        ],
    },
    {
        "condition": lambda ndvi, temp, moisture: temp is not None and temp > 38,
        "suggestions": [
            "Install shade netting for sensitive crops",
            "Irrigate during cooler hours (early morning or evening)",
        ],
    },
    {
        "condition": lambda ndvi, temp, moisture: moisture is not None and moisture < 20,
        "suggestions": [
            "Switch to drip irrigation immediately",
            "Apply mulch to retain soil moisture",
        ],
    },
    {
        "condition": lambda ndvi, temp, moisture: ndvi is not None and 0.3 <= ndvi < 0.6,
        "suggestions": [
            "Apply nitrogen fertilizer (urea)",
            "Monitor pest activity",
            "Ensure adequate drainage",
        ],
    },
    {
        "condition": lambda ndvi, temp, moisture: ndvi is not None and ndvi >= 0.6,
        "suggestions": [
            "Continue current management practices",
            "Prepare for expected good yield",
        ],
    },
]


# ── AI Pipeline: ML-based crop predictor ────────────────────────────────────

# Simple rule-based score table used as fallback
_CROP_RULES: Dict[str, Any] = {
    "rice":       dict(n=(60,140), p=(20,60),  k=(30,80),  temp=(22,35), hum=(70,95),  rain=(150,400)),
    "maize":      dict(n=(50,120), p=(30,80),  k=(40,100), temp=(18,32), hum=(50,80),  rain=(100,300)),
    "cotton":     dict(n=(40,100), p=(20,60),  k=(30,80),  temp=(25,38), hum=(40,70),  rain=(60,200)),
    "soybean":    dict(n=(20,60),  p=(40,100), k=(40,100), temp=(18,30), hum=(50,80),  rain=(100,300)),
    "wheat":      dict(n=(40,120), p=(20,80),  k=(20,80),  temp=(15,25), hum=(40,70),  rain=(50,200)),
    "barley":     dict(n=(30,100), p=(20,60),  k=(20,60),  temp=(12,25), hum=(40,65),  rain=(40,150)),
    "mustard":    dict(n=(40,100), p=(30,80),  k=(20,60),  temp=(15,28), hum=(40,65),  rain=(30,150)),
    "gram":       dict(n=(15,40),  p=(30,80),  k=(20,60),  temp=(15,30), hum=(40,65),  rain=(30,100)),
    "watermelon": dict(n=(30,80),  p=(20,60),  k=(30,80),  temp=(28,40), hum=(30,60),  rain=(10,80)),
    "cucumber":   dict(n=(30,80),  p=(20,60),  k=(30,80),  temp=(25,38), hum=(40,70),  rain=(20,100)),
}


def _rule_score(name: str, n: float, p: float, k: float, temp: float, hum: float, rain: float) -> float:
    """Score crop fit 0.0-1.0 using simple range checks."""
    r = _CROP_RULES[name]
    def s(v: float, lo: float, hi: float) -> float:
        if lo <= v <= hi: return 1.0
        if v < lo:  return max(0.0, 1.0 - (lo - v) / max(lo, 1))
        return max(0.0, 1.0 - (v - hi) / max(hi, 1))
    return (s(n,*r["n"]) + s(p,*r["p"]) + s(k,*r["k"]) +
            s(temp,*r["temp"]) + s(hum,*r["hum"]) + s(rain,*r["rain"])) / 6


def predict_crop_from_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI Pipeline Step: Run the ML model on aggregated field data.

    Input: structured dict from collect_field_data()
    Output: {
        "recommended_crop": str,
        "confidence": float (0-100),
        "alternatives": list[str],
        "model_used": str
    }

    Flow:
      1. Try RandomForest ML model (app/ml/prediction_service.py)
      2. If model fails → rule-based scoring fallback
    """
    n    = float(data.get("n", 80))
    p    = float(data.get("p", 50))
    k    = float(data.get("k", 80))
    temp = float(data.get("temperature", 25))
    hum  = float(data.get("humidity", 60))
    rain = float(data.get("rainfall", 100))
    ndvi = float(data.get("ndvi", 0.45))

    # ── 1. Try ML model ───────────────────────────────────────────────────────
    try:
        from app.ml.prediction_service import predict_crop  # type: ignore
        ml = predict_crop(N=n, P=p, K=k, temperature=temp, humidity=hum, rainfall=rain, ndvi=ndvi)
        top3      = ml.get("top_3", [])
        best_crop = (ml.get("recommended_crop") or "").lower()
        conf      = round(float(ml.get("confidence", 0.5)) * 100, 1)
        alts      = [e["crop"].lower() for e in top3 if e["crop"].lower() != best_crop][:2]
        return {
            "recommended_crop": best_crop,
            "confidence":       min(95.0, max(25.0, conf)),
            "alternatives":     alts,
            "model_used":       "RandomForest-ML",
        }
    except Exception as exc:
        print(f"[recommendation_service] ML model failed, using rule-based: {exc}")

    # ── 2. Rule-based fallback ────────────────────────────────────────────────
    scores = {
        c: _rule_score(c, n, p, k, temp, hum, rain)
        for c in _CROP_RULES
    }
    ranked    = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_crop = ranked[0][0]
    best_sc   = ranked[0][1]
    alts      = [c for c, _ in ranked[1:3]]
    conf      = round(min(95.0, max(25.0, best_sc * 100 * (0.7 + 0.3 * ndvi))), 1)
    return {
        "recommended_crop": best_crop,
        "confidence":       conf,
        "alternatives":     alts,
        "model_used":       "rule-based-fallback",
    }


def generate_suggestions(
    ndvi: Optional[float],
    temperature: Optional[float] = None,
    soil_moisture: Optional[float] = None,
) -> List[str]:
    all_suggestions: List[str] = []
    for rule in SUGGESTION_RULES:
        try:
            if rule["condition"](ndvi, temperature, soil_moisture):
                all_suggestions.extend(rule["suggestions"])
        except Exception:
            continue
    return list(set(all_suggestions))


def estimate_yield(ndvi: Optional[float]) -> str:
    if ndvi is None:
        return "Insufficient data for yield estimation"
    if ndvi > 0.6:
        return "High yield expected (> 80% of potential)"
    elif ndvi >= 0.3:
        return "Moderate yield expected (40-80% of potential)"
    else:
        return "Low yield expected (< 40% of potential)"


async def save_recommendation(
    farmer_id: str,
    field_id: str,
    corridor_id: str,
    ndvi: Optional[float] = None,
    temperature: Optional[float] = None,
    soil_moisture: Optional[float] = None,
    predicted_crop: Optional[str] = None,
) -> dict:
    db = get_db()
    suggestions = generate_suggestions(ndvi, temperature, soil_moisture)
    expected_yield = estimate_yield(ndvi)

    doc = RecommendationModel.document(
        farmer_id=farmer_id,
        field_id=field_id,
        corridor_id=corridor_id,
        suggestions=suggestions,
        predicted_crop=predicted_crop,
        expected_yield=expected_yield,
    )
    result = await db[RecommendationModel.collection].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc


async def get_recommendations_by_field(field_id: str) -> List[dict]:
    db = get_db()
    recs = (
        await db[RecommendationModel.collection]
        .find({"field_id": field_id})
        .sort("created_at", -1)
        .to_list(length=100)
    )
    return [_serialize(r) for r in recs]


def _serialize(r: dict) -> dict:
    r = dict(r)
    r["id"] = str(r.pop("_id"))
    return r