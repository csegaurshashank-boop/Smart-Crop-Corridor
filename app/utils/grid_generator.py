from typing import List, Dict
import string


def generate_grid_corridors(
    field_id: str,
    center_lat: float,
    center_lng: float,
    area_hectares: float,
    grid_size: int = 5,
) -> List[Dict]:
    """
    Generates a grid_size x grid_size corridor grid around the field center.
    Each corridor is a rectangular bounding polygon based on area subdivision.
    """
    # Approximate degree offsets per hectare (rough estimation)
    side_km = (area_hectares * 0.01) ** 0.5  # area in km²
    half_side_lat = (side_km / 111.0) / 2
    half_side_lng = (side_km / (111.0 * abs(cos_approx(center_lat)))) / 2

    cell_lat = (half_side_lat * 2) / grid_size
    cell_lng = (half_side_lng * 2) / grid_size

    row_labels = list(string.ascii_uppercase[:grid_size])
    corridors = []

    for r_idx, row in enumerate(row_labels):
        for c_idx in range(1, grid_size + 1):
            grid_position = f"{row}{c_idx}"

            min_lat = center_lat - half_side_lat + r_idx * cell_lat
            max_lat = min_lat + cell_lat
            min_lng = center_lng - half_side_lng + (c_idx - 1) * cell_lng
            max_lng = min_lng + cell_lng

            # GeoJSON-style polygon coordinates [lng, lat]
            coordinates = [
                [min_lng, min_lat],
                [max_lng, min_lat],
                [max_lng, max_lat],
                [min_lng, max_lat],
                [min_lng, min_lat],  # close polygon
            ]

            corridors.append(
                {
                    "field_id": field_id,
                    "grid_position": grid_position,
                    "coordinates": coordinates,
                    "ndvi": 0.0,
                    "health_status": "unknown",
                    "risk_level": "unknown",
                }
            )

    return corridors


def cos_approx(degrees: float) -> float:
    import math
    return math.cos(math.radians(degrees))