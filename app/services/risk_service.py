from typing import List, Dict, Optional


RISK_RULES = [
    {
        "id": "crop_stress",
        "condition": lambda ndvi, temp, moisture: ndvi is not None and ndvi < 0.3,
        "message": "Crop stress detected. NDVI is critically low. Increase irrigation immediately.",
        "severity": "high",
    },
    {
        "id": "heat_stress",
        "condition": lambda ndvi, temp, moisture: temp is not None and temp > 38,
        "message": f"Heat stress detected. Temperature exceeds safe threshold. Consider shade netting.",
        "severity": "medium",
    },
    {
        "id": "drought_risk",
        "condition": lambda ndvi, temp, moisture: moisture is not None and moisture < 20,
        "message": "Drought risk detected. Soil moisture critically low. Apply drip irrigation.",
        "severity": "high",
    },
    {
        "id": "moderate_health",
        "condition": lambda ndvi, temp, moisture: ndvi is not None and 0.3 <= ndvi < 0.6,
        "message": "Crop health is moderate. Monitor closely and consider nitrogen supplementation.",
        "severity": "low",
    },
]


def detect_risks(
    ndvi: Optional[float],
    temperature: Optional[float] = None,
    soil_moisture: Optional[float] = None,
) -> List[Dict]:
    """
    Evaluate all risk rules and return triggered risks.
    """
    triggered = []
    for rule in RISK_RULES:
        try:
            if rule["condition"](ndvi, temperature, soil_moisture):
                triggered.append(
                    {
                        "risk_id": rule["id"],
                        "message": rule["message"],
                        "severity": rule["severity"],
                    }
                )
        except Exception:
            continue
    return triggered