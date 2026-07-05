from typing import List, Dict


def corridors_to_geojson(corridors: List[Dict]) -> Dict:
    """Convert corridor documents to GeoJSON FeatureCollection."""
    features = []

    for c in corridors:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [c["coordinates"]],
            },
            "properties": {
                "corridor_id": str(c.get("id", c.get("_id", ""))),
                "grid_position": c["grid_position"],
                "ndvi": c["ndvi"],
                "health_status": c["health_status"],
                "risk_level": c["risk_level"],
                "color": ndvi_to_color(c["ndvi"]),
            },
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def ndvi_to_color(ndvi: float) -> str:
    if ndvi > 0.6:
        return "#22c55e"   # green
    elif ndvi >= 0.3:
        return "#eab308"   # yellow
    else:
        return "#ef4444"   # red


def corridors_to_heatmap(corridors: List[Dict]) -> List[Dict]:
    """Return NDVI heatmap data per corridor."""
    return [
        {
            "grid_position": c["grid_position"],
            "ndvi": c["ndvi"],
            "health_status": c["health_status"],
            "color": ndvi_to_color(c["ndvi"]),
            "coordinates": c["coordinates"],
        }
        for c in corridors
    ]