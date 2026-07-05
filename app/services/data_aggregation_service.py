"""
app/services/data_aggregation_service.py

Data Aggregation Service for the AI Pipeline:
  Satellite (NDVI) → Weather API → Soil API → structured ML input

APIs used:
  - NDVI        : Stored corridor data (computed from Sentinel-2 simulation)
                  Real Sentinel Hub integration ready via SENTINEL_HUB_TOKEN env var
  - Weather     : Open-Meteo API (https://api.open-meteo.com) — FREE, no API key
  - Soil        : SoilGrids ISRIC API (https://rest.isric.org) — FREE, no API key
                  Fallback → coordinate-seeded simulation

Caching:
  Simple in-memory TTL cache (1 hour) to avoid hammering external APIs
  on repeated analysis runs for the same field.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from typing import Any, Optional

import httpx
from bson import ObjectId  # type: ignore[import-untyped]

from app.database import get_db  # type: ignore

# ── TTL Cache ────────────────────────────────────────────────────────────────
# Structure: { cache_key: (timestamp, data) }
_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour


def _cache_get(key: str) -> Optional[Any]:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < _CACHE_TTL_SECONDS:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (time.time(), data)


# ── Weather: Open-Meteo (FREE, no API key) ───────────────────────────────────

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_WEATHER_PARAMS = (
    "temperature_2m_max,temperature_2m_min,"
    "relative_humidity_2m_max,relative_humidity_2m_min,"
    "precipitation_sum,rain_sum"
)


async def _fetch_weather_open_meteo(lat: float, lng: float) -> Optional[dict]:
    """
    Fetch 1-day weather forecast from Open-Meteo (completely free, no API key).
    Returns: { temperature, humidity, rainfall }
    Falls back to None on any network/parse error.
    """
    cache_key = f"weather:{round(lat, 4)}:{round(lng, 4)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    params = {
        "latitude":  lat,
        "longitude": lng,
        "daily":     _WEATHER_PARAMS,
        "timezone":  "Asia/Kolkata",
        "forecast_days": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            body = resp.json()

        daily = body.get("daily", {})
        temp_max  = (daily.get("temperature_2m_max")  or [None])[0]
        temp_min  = (daily.get("temperature_2m_min")  or [None])[0]
        hum_max   = (daily.get("relative_humidity_2m_max")  or [None])[0]
        hum_min   = (daily.get("relative_humidity_2m_min")  or [None])[0]
        rain_sum  = (daily.get("precipitation_sum")   or [None])[0]

        if None in (temp_max, temp_min, hum_max, hum_min):
            return None

        result = {
            "temperature": round((temp_max + temp_min) / 2, 1),
            "humidity":    round((hum_max  + hum_min)  / 2, 1),
            "rainfall":    round(float(rain_sum or 0), 1),
            "source":      "open-meteo",
        }
        _cache_set(cache_key, result)
        return result

    except Exception as exc:
        print(f"[data_aggregation] Open-Meteo weather fetch failed: {exc}")
        return None


# ── Soil: SoilGrids ISRIC (FREE, no API key) ─────────────────────────────────

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
_SOIL_PROPERTIES = "nitrogen,phh2o,soc,clay,sand,ocd"


async def _fetch_soil_soilgrids(lat: float, lng: float) -> Optional[dict]:
    """
    Fetch top-soil (0-5 cm) data from SoilGrids v2 ISRIC API.
    Returns approximated { n, p, k, soil_moisture } or None on failure.

    SoilGrids provides:
      nitrogen (cg/kg)  → convert to kg/ha (~N)
      phh2o (0.1 pH)    → soil pH
      soc (dg/kg)       → soil organic carbon (used to approximate P, K)
      clay (g/kg)       → texture (affects moisture retention)
    """
    cache_key = f"soil:{round(lat, 4)}:{round(lng, 4)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    params = {
        "lon":        lng,
        "lat":        lat,
        "property":   _SOIL_PROPERTIES,
        "depth":      "0-5cm",
        "value":      "mean",
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(SOILGRIDS_URL, params=params)
            resp.raise_for_status()
            body = resp.json()

        props = body.get("properties", {})
        layers = props.get("layers", [])

        raw: dict[str, Optional[float]] = {}
        for layer in layers:
            name = layer.get("name")
            depths = layer.get("depths", [{}])
            val = depths[0].get("values", {}).get("mean") if depths else None
            raw[name] = float(val) if val is not None else None

        # Convert units → agronomic ranges
        # nitrogen in cg/kg  → typical range 500-2000 → map to 40-140 kg/ha
        n_raw = raw.get("nitrogen")
        n = round(_scale(n_raw or 1000, 200, 3000, 40, 140), 1)

        # SOC (dg/kg) correlates roughly with P & K availability
        soc = raw.get("soc")
        p = round(_scale(soc or 50, 0, 200, 20, 100), 1)
        k = round(_scale(soc or 50, 0, 200, 30, 180), 1)

        # clay (g/kg) affects moisture retention
        clay = raw.get("clay")
        soil_moisture = round(_scale(clay or 200, 50, 600, 15, 60), 1)

        result = {
            "n":            n,
            "p":            p,
            "k":            k,
            "soil_moisture": soil_moisture,
            "ph":           round((raw.get("phh2o") or 65) / 10, 2),  # phh2o in 0.1 pH units
            "source":       "soilgrids",
        }
        _cache_set(cache_key, result)
        return result

    except Exception as exc:
        print(f"[data_aggregation] SoilGrids fetch failed: {exc}")
        return None


def _scale(val: float, in_lo: float, in_hi: float, out_lo: float, out_hi: float) -> float:
    """Linear scale from input range to output range, clamped."""
    if in_hi == in_lo:
        return (out_lo + out_hi) / 2
    ratio = max(0.0, min(1.0, (val - in_lo) / (in_hi - in_lo)))
    return out_lo + ratio * (out_hi - out_lo)


# ── Sentinel Hub NDVI (optional, requires token) ─────────────────────────────

SENTINEL_HUB_TOKEN = os.getenv("SENTINEL_HUB_TOKEN", "")
SENTINEL_PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"


async def _fetch_ndvi_sentinel_hub(lat: float, lng: float) -> Optional[float]:
    """
    Fetch real NDVI from Sentinel Hub (Copernicus Sentinel-2).
    Requires SENTINEL_HUB_TOKEN env var.
    Returns average NDVI float or None if token missing / request fails.
    """
    if not SENTINEL_HUB_TOKEN:
        return None

    cache_key = f"ndvi_sh:{round(lat, 3)}:{round(lng, 3)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # Small 0.01° bounding box around the point
    bbox = [lng - 0.005, lat - 0.005, lng + 0.005, lat + 0.005]
    payload = {
        "input": {
            "bounds": {"bbox": bbox, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
            "data": [{"type": "sentinel-2-l2a", "dataFilter": {"maxCloudCoverage": 30}}],
        },
        "output": {"width": 32, "height": 32, "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]},
        "evalscript": (
            "//VERSION=3\n"
            "function setup(){return{input:['B04','B08'],output:{bands:1,sampleType:'FLOAT32'}}}\n"
            "function evaluatePixel(s){"
            "  let ndvi=(s.B08-s.B04)/(s.B08+s.B04+1e-10);"
            "  return[ndvi];"
            "}"
        ),
    }
    headers = {"Authorization": f"Bearer {SENTINEL_HUB_TOKEN}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(SENTINEL_PROCESS_URL, json=payload, headers=headers)
            resp.raise_for_status()
        # Response is a GeoTIFF binary — parse mean pixel value
        # Requires rasterio; gracefully fall through if not installed
        try:
            import io
            import numpy as np
            import rasterio  # type: ignore
            with rasterio.open(io.BytesIO(resp.content)) as src:
                data = src.read(1).astype(float)
                data = data[~np.isnan(data)]
                ndvi_val = float(np.mean(np.clip(data, -1, 1))) if data.size else None
        except ImportError:
            # rasterio not installed — parse header X-NDVI-Mean if available
            ndvi_val = None

        if ndvi_val is not None:
            _cache_set(cache_key, ndvi_val)
        return ndvi_val
    except Exception as exc:
        print(f"[data_aggregation] Sentinel Hub NDVI fetch failed: {exc}")
        return None


# ── Simulation fallbacks ──────────────────────────────────────────────────────

def _simulate_weather(lat: float, lng: float, season: str) -> dict:
    """Coordinate + season seeded weather simulation."""
    from app.services.satellite_service import simulate_environmental_conditions  # type: ignore
    env = simulate_environmental_conditions(lat, lng, season)
    return {
        "temperature": env["temperature"],
        "humidity":    env["humidity"],
        "rainfall":    env["rainfall"],
        "source":      "simulation",
    }


def _simulate_soil(lat: float, lng: float) -> dict:
    """Coordinate-seeded soil simulation."""
    seed = int(abs(lat * 1373 + lng * 3571)) % 99991
    rng  = random.Random(seed)
    return {
        "n":            round(rng.uniform(40, 140), 1),
        "p":            round(rng.uniform(20, 100), 1),
        "k":            round(rng.uniform(20, 200), 1),
        "soil_moisture": round(rng.uniform(15, 60), 1),
        "ph":           round(rng.uniform(5.5, 8.0), 2),
        "source":       "simulation",
    }


# ── NDVI from stored corridor data ───────────────────────────────────────────

async def _get_ndvi_from_corridors(field_id: str, lat: float, lng: float) -> float:
    """
    Primary: average NDVI from already-computed corridor docs in DB.
    Secondary: try Sentinel Hub if token available.
    Tertiary: simulate from grid position hash.
    """
    db = get_db()

    # 1. Use stored corridor NDVI values (most recent analysis)
    corridors = await db["corridors"].find(
        {"field_id": field_id, "ndvi": {"$exists": True}}
    ).to_list(length=500)

    if corridors:
        values = [c["ndvi"] for c in corridors if isinstance(c.get("ndvi"), (int, float))]
        if values:
            return round(sum(values) / len(values), 3)

    # 2. Try CDSE real Sentinel-2 NDVI (Copernicus Data Space)
    try:
        from app.services.ndvi_cdse_service import get_ndvi_from_cdse  # type: ignore
        cdse_ndvi = await get_ndvi_from_cdse(lat, lng)
        if cdse_ndvi is not None:
            return round(cdse_ndvi, 3)
    except Exception as _cdse_exc:
        print(f"[data_aggregation] CDSE NDVI skipped: {_cdse_exc}")

    # 3. Simulation fallback
    from app.services.satellite_service import simulate_ndvi_for_corridor  # type: ignore
    return simulate_ndvi_for_corridor(f"{round(lat, 3)}_{round(lng, 3)}")


# ── Main public function ──────────────────────────────────────────────────────

async def collect_field_data(field_id: str) -> dict:
    """
    Collect all data needed for the ML crop prediction pipeline.

    Pipeline:
      1. Fetch field location (lat, lng) from MongoDB
      2. Get NDVI → stored corridors → Sentinel Hub → simulation
      3. Get Weather → Open-Meteo API → simulation
      4. Get Soil → SoilGrids API → simulation
      5. Merge and return structured ML input dict

    Returns:
    {
        "n": float,           # Nitrogen (kg/ha)
        "p": float,           # Phosphorus (kg/ha)
        "k": float,           # Potassium (kg/ha)
        "temperature": float, # °C
        "humidity": float,    # %
        "rainfall": float,    # mm
        "ndvi": float,        # 0.0 – 1.0
        "soil_moisture": float,
        "ph": float,
        "data_sources": dict  # which APIs were used
    }
    """
    db = get_db()
    field = await db["fields"].find_one({"_id": ObjectId(field_id)})
    if not field:
        raise ValueError(f"Field {field_id} not found")

    loc = field.get("location") or field.get("center") or {}
    lat = float(loc.get("lat", 25.43))
    lng = float(loc.get("lng", 81.84))

    # Detect current season for simulation fallback
    from app.services.season_service import detect_season  # type: ignore
    season = detect_season()

    # ── Run all API calls concurrently ────────────────────────────────────────
    ndvi_task    = _get_ndvi_from_corridors(field_id, lat, lng)
    weather_task = _fetch_weather_open_meteo(lat, lng)
    soil_task    = _fetch_soil_soilgrids(lat, lng)

    ndvi, weather_data, soil_data = await asyncio.gather(
        ndvi_task, weather_task, soil_task,
        return_exceptions=True,
    )

    # Handle exceptions from gather
    if isinstance(ndvi, Exception):
        ndvi = 0.45  # neutral NDVI

    if isinstance(weather_data, Exception) or weather_data is None:
        weather_data = _simulate_weather(lat, lng, season)

    if isinstance(soil_data, Exception) or soil_data is None:
        soil_data = _simulate_soil(lat, lng)

    # ── Merge all sources ─────────────────────────────────────────────────────
    return {
        # Soil nutrients
        "n":            soil_data["n"],
        "p":            soil_data["p"],
        "k":            soil_data["k"],
        "soil_moisture": soil_data["soil_moisture"],
        "ph":           soil_data.get("ph", 6.5),
        # Weather
        "temperature":  weather_data["temperature"],
        "humidity":     weather_data["humidity"],
        "rainfall":     weather_data["rainfall"],
        # Satellite
        "ndvi":         float(ndvi),
        # Provenance (for logging / debugging)
        "data_sources": {
            "ndvi":    "corridors_db" if ndvi else "simulation",
            "weather": weather_data.get("source", "unknown"),
            "soil":    soil_data.get("source", "unknown"),
        },
    }
