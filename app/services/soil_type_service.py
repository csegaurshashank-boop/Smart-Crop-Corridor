"""
app/services/soil_type_service.py

Infer soil type from geographic coordinates using Indian soil region mapping.
No external API needed — uses deterministic lat/lng region lookup.
"""
import random


# ── Indian Soil Regions (simplified geographic mapping) ───────────────────────
# Based on major soil belts across India
SOIL_REGIONS = [
    # Indo-Gangetic Plain — Alluvial
    {"lat_range": (24, 31), "lng_range": (76, 88), "soil": "alluvial",
     "description": "Rich alluvial soil from river deposits, highly fertile"},
    # Deccan Plateau — Black (Regur)
    {"lat_range": (15, 22), "lng_range": (73, 80), "soil": "black",
     "description": "Black cotton soil (regur), rich in minerals, retains moisture"},
    # South India — Red/Laterite
    {"lat_range": (8, 16), "lng_range": (74, 80), "soil": "red",
     "description": "Red soil formed from crystalline rock, moderately fertile"},
    # Western Ghats — Laterite
    {"lat_range": (10, 20), "lng_range": (72, 76), "soil": "laterite",
     "description": "Laterite soil formed in tropical climate, rich in iron/aluminum"},
    # Rajasthan — Sandy/Arid
    {"lat_range": (24, 30), "lng_range": (68, 76), "soil": "sandy",
     "description": "Sandy arid soil, low moisture retention, needs irrigation"},
    # Punjab/Haryana — Alluvial
    {"lat_range": (28, 33), "lng_range": (74, 78), "soil": "alluvial",
     "description": "Rich alluvial soil ideal for wheat, rice, and sugarcane"},
    # Northeast — Laterite/Loamy
    {"lat_range": (22, 28), "lng_range": (88, 97), "soil": "loamy",
     "description": "Loamy soil with good drainage and organic content"},
    # Coastal regions — Sandy Loam
    {"lat_range": (8, 22), "lng_range": (80, 87), "soil": "clay",
     "description": "Clayey soil with high water retention capacity"},
]

# Soil properties database
SOIL_PROPERTIES = {
    "alluvial": {
        "description": "Rich alluvial soil from river deposits, highly fertile",
        "ph_range": (6.5, 7.5),
        "organic_carbon": "medium to high",
        "water_retention": "good",
        "drainage": "well-drained",
        "suitable_crops": ["wheat", "rice", "maize", "sugarcane", "cotton", "potato"],
    },
    "black": {
        "description": "Black cotton soil (regur), rich in minerals, retains moisture",
        "ph_range": (7.0, 8.5),
        "organic_carbon": "low to medium",
        "water_retention": "very high",
        "drainage": "poor (cracks when dry)",
        "suitable_crops": ["cotton", "sugarcane", "wheat", "soybean", "jowar"],
    },
    "red": {
        "description": "Red soil formed from crystalline rock, moderately fertile",
        "ph_range": (5.5, 7.0),
        "organic_carbon": "low",
        "water_retention": "low",
        "drainage": "well-drained",
        "suitable_crops": ["groundnut", "potato", "maize", "rice", "tobacco"],
    },
    "laterite": {
        "description": "Laterite soil rich in iron/aluminum, formed in tropical climate",
        "ph_range": (5.0, 6.5),
        "organic_carbon": "low",
        "water_retention": "low to medium",
        "drainage": "excessively drained",
        "suitable_crops": ["tea", "coffee", "cashew", "rubber", "coconut"],
    },
    "sandy": {
        "description": "Sandy arid soil with low moisture, needs irrigation",
        "ph_range": (7.0, 8.5),
        "organic_carbon": "very low",
        "water_retention": "very low",
        "drainage": "excessively drained",
        "suitable_crops": ["bajra", "jowar", "groundnut", "guar", "mustard"],
    },
    "clay": {
        "description": "Clayey soil with high water retention, compact structure",
        "ph_range": (6.0, 7.5),
        "organic_carbon": "medium",
        "water_retention": "very high",
        "drainage": "poor",
        "suitable_crops": ["rice", "sugarcane", "jute", "cotton"],
    },
    "loamy": {
        "description": "Loamy soil with balanced texture, ideal for most crops",
        "ph_range": (6.0, 7.0),
        "organic_carbon": "high",
        "water_retention": "good",
        "drainage": "well-drained",
        "suitable_crops": ["wheat", "rice", "maize", "vegetables", "fruits"],
    },
}


def infer_soil_type(lat: float, lng: float) -> str:
    """Infer soil type from geographic coordinates."""
    for region in SOIL_REGIONS:
        lat_range: tuple = region["lat_range"]  # type: ignore
        lng_range: tuple = region["lng_range"]  # type: ignore
        lat_lo, lat_hi = float(lat_range[0]), float(lat_range[1])
        lng_lo, lng_hi = float(lng_range[0]), float(lng_range[1])
        if lat_lo <= lat <= lat_hi and lng_lo <= lng <= lng_hi:
            return str(region["soil"])

    # Fallback: deterministic based on coordinates
    seed = int(abs(lat * 100 + lng * 100)) % len(SOIL_PROPERTIES)
    return list(SOIL_PROPERTIES.keys())[seed]


def get_soil_properties(soil_type: str) -> dict:
    """Get detailed properties of a soil type."""
    props: dict = SOIL_PROPERTIES.get(soil_type, SOIL_PROPERTIES["loamy"])  # type: ignore
    return {"soil_type": soil_type, **props}


def get_soil_crop_boost(crop: str, soil_type: str) -> float:
    """Returns a multiplier (0.6–1.2) for how well a crop matches the soil type."""
    props: dict = SOIL_PROPERTIES.get(soil_type, SOIL_PROPERTIES["loamy"])  # type: ignore
    crop_list: list = props.get("suitable_crops", [])  # type: ignore
    suitable = [str(c).lower() for c in crop_list]
    if crop.lower() in suitable:
        return 1.2
    return 0.8

