"""
app/services/irrigation_service.py

Irrigation monitoring and smart alert system.
Monitors soil moisture, rainfall probability, crop growth stage
and generates irrigation recommendations.
"""
import random
from datetime import datetime, timedelta
from bson import ObjectId  # type: ignore[import-untyped]

from app.database import get_db  # type: ignore
from app.services.season_service import detect_season  # type: ignore


# ── Crop water requirements (mm/day at peak growth) ─────────────────────────
CROP_WATER_NEEDS = {
    "rice":       {"daily_mm": 8.0,  "critical_moisture": 40, "growth_days": 130},
    "wheat":      {"daily_mm": 4.5,  "critical_moisture": 25, "growth_days": 135},
    "maize":      {"daily_mm": 5.5,  "critical_moisture": 30, "growth_days": 110},
    "cotton":     {"daily_mm": 5.0,  "critical_moisture": 28, "growth_days": 170},
    "sugarcane":  {"daily_mm": 7.0,  "critical_moisture": 35, "growth_days": 360},
    "soybean":    {"daily_mm": 4.0,  "critical_moisture": 25, "growth_days": 100},
}

DEFAULT_WATER = {"daily_mm": 5.0, "critical_moisture": 30, "growth_days": 120}


def _estimate_growth_stage(days_since_sowing: int, total_days: int) -> dict:
    """Estimate current crop growth stage based on elapsed days."""
    pct = min(100, (days_since_sowing / total_days) * 100)  # type: ignore

    if pct < 15:
        return {"stage": "Germination / Seedling", "water_factor": 0.6, "stage_pct": round(pct)}  # type: ignore
    elif pct < 35:
        return {"stage": "Vegetative Growth", "water_factor": 0.8, "stage_pct": round(pct)}  # type: ignore
    elif pct < 55:
        return {"stage": "Flowering / Reproductive", "water_factor": 1.2, "stage_pct": round(pct)}  # type: ignore
    elif pct < 75:
        return {"stage": "Grain Filling / Fruiting", "water_factor": 1.0, "stage_pct": round(pct)}  # type: ignore
    elif pct < 90:
        return {"stage": "Maturation", "water_factor": 0.5, "stage_pct": round(pct)}  # type: ignore
    else:
        return {"stage": "Ready for Harvest", "water_factor": 0.2, "stage_pct": round(pct)}  # type: ignore


def _irrigation_time_recommendation(temp: float) -> dict:
    """Recommend best irrigation time based on temperature."""
    if temp > 35:
        return {
            "best_time": "Evening (5:00 PM - 7:00 PM)",
            "avoid": "Midday irrigation — high evaporation loss",
            "reason": "High temperature detected. Evening irrigation reduces evaporation by 30-40%."
        }
    elif temp > 25:
        return {
            "best_time": "Early Morning (6:00 AM - 8:00 AM)",
            "alternative": "Evening (5:00 PM - 7:00 PM)",
            "reason": "Morning irrigation allows water to reach roots before heat reduces absorption."
        }
    else:
        return {
            "best_time": "Morning (7:00 AM - 10:00 AM)",
            "reason": "Cool conditions — morning irrigation gives optimal absorption with minimal disease risk."
        }


async def generate_irrigation_alert(field_id: str) -> dict:
    """
    Analyze field conditions and generate irrigation recommendation.
    Returns a structured irrigation status + alert if needed.
    """
    db = get_db()
    field = await db["fields"].find_one({"_id": ObjectId(field_id)})
    if not field:
        return {"error": "Field not found"}

    analysis = field.get("land_analysis", {})
    crop = field.get("recommended_crop", "wheat")
    farmer_id = field.get("farmer_id", "unknown")

    # Current conditions
    soil_moisture = analysis.get("soil_moisture", 35)
    temperature   = analysis.get("temperature", 28)
    humidity      = analysis.get("humidity", 60)
    rainfall      = analysis.get("rainfall", 100)

    # Crop-specific needs
    crop_lower = crop.lower() if crop else "wheat"
    needs = CROP_WATER_NEEDS.get(crop_lower, DEFAULT_WATER)
    critical_moisture = needs["critical_moisture"]
    daily_water_mm    = needs["daily_mm"]

    # Estimate rainfall probability (simulated from current conditions)
    season = detect_season()
    if season == "kharif":
        rainfall_probability = min(85, max(20, humidity * 0.9 + random.uniform(-10, 10)))  # type: ignore
    elif season == "rabi":
        rainfall_probability = min(40, max(5, humidity * 0.3 + random.uniform(-5, 5)))  # type: ignore
    else:  # zaid
        rainfall_probability = min(25, max(5, humidity * 0.2 + random.uniform(-5, 5)))  # type: ignore
    rainfall_probability = round(rainfall_probability, 1)  # type: ignore

    # Estimate days since sowing (approximate from created_at)
    created = field.get("created_at", datetime.utcnow())
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created)
        except Exception:
            created = datetime.utcnow()
    days_since = (datetime.utcnow() - created).days
    growth = _estimate_growth_stage(days_since, needs["growth_days"])  # type: ignore

    # Irrigation time recommendation
    timing = _irrigation_time_recommendation(temperature)

    # ── Core alert logic ────────────────────────────────────────────────────
    needs_irrigation = False
    urgency = "low"
    message = ""
    water_quantity = 0

    if soil_moisture < critical_moisture and rainfall_probability < 40:
        needs_irrigation = True
        urgency = "high" if soil_moisture < critical_moisture * 0.7 else "medium"
        deficit = critical_moisture - soil_moisture
        water_quantity = round(daily_water_mm * growth["water_factor"] * field.get("area", 1) * 10, 0)  # type: ignore  # liters/ha
        message = (
            f"Soil moisture ({soil_moisture:.0f}%) is below critical level ({critical_moisture}%) "
            f"and rainfall probability is low ({rainfall_probability:.0f}%). "
            f"Immediate irrigation recommended."
        )
    elif soil_moisture < critical_moisture * 1.2 and rainfall_probability < 50:
        needs_irrigation = True
        urgency = "low"
        water_quantity = round(daily_water_mm * growth["water_factor"] * field.get("area", 1) * 8, 0)  # type: ignore
        message = (
            f"Soil moisture ({soil_moisture:.0f}%) is approaching critical level. "
            f"Plan irrigation within 2-3 days if no rain occurs."
        )
    else:
        message = (
            f"Soil moisture ({soil_moisture:.0f}%) is adequate. "
            f"No immediate irrigation needed."
        )
        if rainfall_probability > 60:
            message += f" Rainfall likely ({rainfall_probability:.0f}% probability)."

    # Calculate next irrigation date
    if needs_irrigation:
        next_irrigation = datetime.utcnow() + timedelta(hours=6 if urgency == "high" else 48)
    else:
        days_until = max(3, int((soil_moisture - critical_moisture) / 2))
        next_irrigation = datetime.utcnow() + timedelta(days=days_until)

    # Build result
    result = {
        "field_id": field_id,
        "crop": crop,
        "needs_irrigation": needs_irrigation,
        "urgency": urgency,
        "message": message,
        "soil_moisture": round(soil_moisture, 1),
        "soil_moisture_critical": critical_moisture,
        "rainfall_probability": rainfall_probability,
        "temperature": round(temperature, 1),
        "growth_stage": growth,
        "timing": timing,
        "water_quantity_liters": water_quantity,
        "next_irrigation": next_irrigation.isoformat(),
        "season": season,
        "checked_at": datetime.utcnow().isoformat(),
    }

    # Save irrigation alert to DB if needed
    if needs_irrigation:
        alert_doc = {
            "farmer_id": farmer_id,
            "field_id": field_id,
            "corridor": "ALL",
            "alert_type": "irrigation",
            "severity": urgency,
            "is_read": False,
            "message": message,
            "irrigation_details": {
                "water_quantity_liters": water_quantity,
                "best_time": timing["best_time"],
                "next_date": next_irrigation.isoformat(),
                "growth_stage": growth["stage"],
            },
            "created_at": datetime.utcnow(),
        }
        await db["alerts"].insert_one(alert_doc)

    return result
