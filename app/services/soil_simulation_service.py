import hashlib
from typing import Dict


def _stable_random(seed_str: str, min_val: float, max_val: float) -> float:
    hash_int = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    normalized = (hash_int % 10000) / 10000.0
    return round(min_val + normalized * (max_val - min_val), 2)


def simulate_soil_parameters(lat: float, lng: float) -> Dict[str, float]:
    loc_key = f"{round(lat, 3)}_{round(lng, 3)}"
    base_temp = 25 - abs(lat - 20) * 0.3
    temperature = round(base_temp + _stable_random(f"{loc_key}_T", -5, 10), 1)
    temperature = max(10.0, min(45.0, temperature))
    return {
        "n": _stable_random(f"{loc_key}_N", 20, 140),
        "p": _stable_random(f"{loc_key}_P", 5, 145),
        "k": _stable_random(f"{loc_key}_K", 5, 205),
        "temperature": temperature,
        "humidity": _stable_random(f"{loc_key}_H", 30, 95),
        "rainfall": _stable_random(f"{loc_key}_R", 50, 400),
        "soil_moisture": _stable_random(f"{loc_key}_SM", 15, 65),
    }


def simulate_corridor_ndvi(grid_position: str, base_lat: float, base_lng: float) -> float:
    seed = f"{round(base_lat, 3)}_{round(base_lng, 3)}_{grid_position}"
    hash_int = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    normalized = (hash_int % 1000) / 1000.0
    if normalized < 0.20:
        ndvi = 0.05 + normalized * 1.25
    elif normalized < 0.55:
        ndvi = 0.30 + (normalized - 0.20) * 0.857
    else:
        ndvi = 0.60 + (normalized - 0.55) * 0.889
    return round(min(0.95, max(0.01, ndvi)), 3)