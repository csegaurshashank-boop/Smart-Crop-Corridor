import numpy as np
import random
import hashlib
from typing import Any, Optional


def calculate_ndvi_from_arrays(red_band: np.ndarray, nir_band: np.ndarray) -> float:
    red = red_band.astype(float)
    nir = nir_band.astype(float)
    denominator = nir + red
    denominator[denominator == 0] = 1e-10
    ndvi_array = (nir - red) / denominator
    ndvi_array = np.clip(ndvi_array, -1, 1)
    return float(np.mean(ndvi_array))


def calculate_ndvi_from_raster(red_path: str, nir_path: str) -> Optional[float]:
    """Requires rasterio — install separately when needed."""
    try:
        import rasterio
        with rasterio.open(red_path) as red_src:
            red_band = red_src.read(1).astype(float)
        with rasterio.open(nir_path) as nir_src:
            nir_band = nir_src.read(1).astype(float)
        return calculate_ndvi_from_arrays(red_band, nir_band)
    except ImportError:
        raise RuntimeError("Rasterio not available. Use simulate_ndvi_for_corridor() instead.")


def simulate_ndvi_for_corridor(grid_position: str) -> float:
    """Simulates realistic NDVI values for testing without satellite data."""
    seed = int(hashlib.md5(grid_position.encode()).hexdigest(), 16) % 100
    return round(0.1 + (seed / 100.0) * 0.75, 3)


# ── Environmental condition simulators ────────────────────────────────────────

def simulate_land_surface_temp(lat: float, lng: float, season: str = "rabi") -> float:
    """Simulate land surface temperature (°C) from coordinates + season."""
    seed = int(abs(lat * 1373 + lng * 3571)) % 99991
    rng  = random.Random(seed)

    base_temps: dict[str, Any] = {
        "kharif": (28, 38),
        "rabi":   (12, 26),
        "zaid":   (32, 44),
    }
    lo, hi = base_temps.get(season) or (20, 35)
    # adjust by latitude (further north = cooler)
    lat_offset = max(0, (lat - 20) * -0.3)
    return round(rng.uniform(lo, hi) + lat_offset, 1)


def simulate_environmental_conditions(lat: float, lng: float, season: str = "rabi") -> dict[str, Any]:
    """
    Simulate comprehensive environmental conditions.
    Returns temperature, humidity, rainfall, soil_moisture, land_surface_temp, rainfall_probability.
    """
    seed = int(abs(lat * 1373 + lng * 3571)) % 99991
    rng  = random.Random(seed)

    season_params: dict[str, Any] = {
        "kharif": {"temp": (25, 35), "hum": (65, 92), "rain": (150, 450), "moisture": (30, 65), "rain_prob": (50, 85)},
        "rabi":   {"temp": (10, 25), "hum": (40, 65), "rain": (15, 80),   "moisture": (20, 45), "rain_prob": (10, 35)},
        "zaid":   {"temp": (30, 42), "hum": (25, 50), "rain": (5, 40),    "moisture": (12, 30), "rain_prob": (5, 20)},
    }
    params: dict[str, Any] = season_params[season] if season in season_params else season_params["rabi"]

    temperature   = round(rng.uniform(*params["temp"]), 1)
    humidity      = round(rng.uniform(*params["hum"]), 1)
    rainfall      = round(rng.uniform(*params["rain"]), 1)
    soil_moisture = round(rng.uniform(*params["moisture"]), 1)
    rain_prob     = round(rng.uniform(*params["rain_prob"]), 1)
    lst           = simulate_land_surface_temp(lat, lng, season)

    return {
        "temperature":        temperature,
        "humidity":           humidity,
        "rainfall":           rainfall,
        "soil_moisture":      soil_moisture,
        "land_surface_temp":  lst,
        "rainfall_probability": rain_prob,
    }