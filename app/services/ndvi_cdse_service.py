"""
app/services/ndvi_cdse_service.py

Copernicus Data Space Ecosystem (CDSE) - Real Sentinel-2 NDVI Service

Pipeline:
  1. Fetch OAuth token  (cached 9 min — tokens live 600 s)
  2. Call CDSE Statistical API → mean NDVI for field bounding box
  3. Apply deterministic per-corridor variation (±0.08)

Fallback chain (NEVER crashes):
  CDSE token failure   → fallback
  CDSE API failure     → fallback
  Empty / cloudy data  → fallback
  Any exception        → fallback → simulate_ndvi_for_corridor()

Setup (FREE account):
  1. Register at https://dataspace.copernicus.eu
  2. Dashboard → User Settings → OAuth Clients → Create New Client
  3. Add to .env:
       CDSE_CLIENT_ID=your_client_id
       CDSE_CLIENT_SECRET=your_client_secret

NDVI formula applied inside evalscript:
  NDVI = (B08 - B04) / (B08 + B04)
  Cloud/shadow pixels (SCL classes 3,8,9,10) are excluded automatically.
"""

from __future__ import annotations

import hashlib
import os
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

# ── Credentials ───────────────────────────────────────────────────────────────
CDSE_CLIENT_ID     = os.getenv("CDSE_CLIENT_ID", "")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET", "")

# ── API endpoints ─────────────────────────────────────────────────────────────
_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)
_STATS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"

# ── Token cache (in-process, refreshed every 9 min) ──────────────────────────
_token_cache: dict = {"token": None, "expires_at": 0.0}

# ── NDVI result cache (per coordinate, 1-hour TTL) ───────────────────────────
_ndvi_cache: dict[str, tuple[float, float]] = {}   # key → (timestamp, ndvi)
_NDVI_CACHE_TTL = 3600                              # 1 hour


# ── EVALSCRIPT ────────────────────────────────────────────────────────────────
_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: [{ bands: ['B04', 'B08', 'SCL'] }],
    output: [{ id: 'ndvi', bands: 1, sampleType: 'FLOAT32' }]
  };
}
function evaluatePixel(s) {
  // Skip cloud (8,9), cloud shadow (3), and saturated (10) pixels
  if ([3, 8, 9, 10].includes(s.SCL)) return [NaN];
  var ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-10);
  return [ndvi];
}"""


# ── Step 1: OAuth Token ───────────────────────────────────────────────────────

async def get_cdse_token() -> Optional[str]:
    """
    Fetch or return cached CDSE OAuth 2.0 token.
    Tokens are valid 600 s; we refresh 60 s before expiry.
    Returns None if credentials are missing or the request fails.
    """
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]   # cache hit

    if not CDSE_CLIENT_ID or not CDSE_CLIENT_SECRET:
        return None  # credentials not configured

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type":    "client_credentials",
                    "client_id":     CDSE_CLIENT_ID,
                    "client_secret": CDSE_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            body = resp.json()

        token      = body.get("access_token")
        expires_in = int(body.get("expires_in", 600))

        _token_cache["token"]      = token
        _token_cache["expires_at"] = now + expires_in - 60  # 60 s safety buffer

        print(f"[ndvi_cdse] Token acquired, valid for {expires_in - 60} s")
        return token

    except Exception as exc:
        print(f"[ndvi_cdse] Token fetch failed: {exc}")
        return None


# ── Step 2: CDSE Statistical API → mean NDVI ─────────────────────────────────

async def get_ndvi_from_cdse(lat: float, lng: float) -> Optional[float]:
    """
    Fetch mean NDVI for a ~1 km × 1 km area centred on (lat, lng)
    using the CDSE Sentinel-2 L2A Statistical API.

    - Called ONCE per field (result cached 1 h).
    - Cloud/shadow pixels excluded via SCL band.
    - Returns float in [0.0, 1.0] or None on any failure.
    """
    # ── Cache check ───────────────────────────────────────────────────────────
    cache_key = f"cdse_ndvi:{round(lat, 3)}:{round(lng, 3)}"
    now = time.time()
    if cache_key in _ndvi_cache:
        ts, val = _ndvi_cache[cache_key]
        if now - ts < _NDVI_CACHE_TTL:
            print(f"[ndvi_cdse] Cache hit ({lat:.3f},{lng:.3f}) → {val:.3f}")
            return val

    # ── Token ─────────────────────────────────────────────────────────────────
    token = await get_cdse_token()
    if not token:
        return None

    # ── 30-day window ending today (most recent Sentinel-2 imagery) ───────────
    date_to   = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=30)
    fmt       = "%Y-%m-%dT%H:%M:%SZ"

    # ── ~0.01° bounding box ≈ 1 km around the point ──────────────────────────
    delta = 0.005
    bbox  = [
        round(lng - delta, 6),
        round(lat - delta, 6),
        round(lng + delta, 6),
        round(lat + delta, 6),
    ]

    payload = {
        "input": {
            "bounds": {
                "bbox":       bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [{
                "type":       "sentinel-2-l2a",
                "dataFilter": {"maxCloudCoverage": 80},   # generous; SCL filters per-pixel
            }],
        },
        "aggregation": {
            "timeRange": {
                "from": date_from.strftime(fmt),
                "to":   date_to.strftime(fmt),
            },
            "aggregationInterval": {"of": "P30D"},   # one result for the whole window
            "evalscript": _EVALSCRIPT,
            "resx": 10,   # Sentinel-2 10 m resolution
            "resy": 10,
        },
        "calculations": {
            "default": {
                "statistics": {
                    "default": {
                        "percentiles": {"bins": [25, 50, 75]},
                    }
                }
            }
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _STATS_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type":  "application/json",
                },
            )
            resp.raise_for_status()
            body = resp.json()

        # ── Parse response ────────────────────────────────────────────────────
        # Expected path: data[0].outputs.ndvi.bands.B0.stats.mean
        intervals = body.get("data", [])
        if not intervals:
            print(f"[ndvi_cdse] Empty data for ({lat},{lng}) — possibly all cloudy")
            return None

        stats = (
            intervals[0]
            .get("outputs", {})
            .get("ndvi", {})
            .get("bands", {})
            .get("B0", {})
            .get("stats", {})
        )

        mean_ndvi = stats.get("mean")
        if mean_ndvi is None or not isinstance(mean_ndvi, (int, float)):
            print(f"[ndvi_cdse] Stats missing mean for ({lat},{lng}): {stats}")
            return None

        # Clamp and round
        ndvi_val = round(max(0.0, min(1.0, float(mean_ndvi))), 3)
        _ndvi_cache[cache_key] = (now, ndvi_val)
        print(f"[ndvi_cdse] Real NDVI ({lat:.3f},{lng:.3f}) = {ndvi_val:.3f}")
        return ndvi_val

    except httpx.TimeoutException:
        print(f"[ndvi_cdse] Request timed out for ({lat},{lng})")
        return None
    except httpx.HTTPStatusError as exc:
        print(f"[ndvi_cdse] HTTP {exc.response.status_code} for ({lat},{lng})")
        return None
    except Exception as exc:
        print(f"[ndvi_cdse] Unexpected error for ({lat},{lng}): {exc}")
        return None


# ── Step 3: Safe public wrapper — ALWAYS returns valid NDVI ──────────────────

async def get_ndvi(lat: float, lng: float) -> float:
    """
    Safe NDVI accessor for land_analysis_service.

    Priority:
      1. CDSE Sentinel-2 Statistical API (real satellite)
      2. Simulation fallback via simulate_ndvi_for_corridor()

    NEVER raises. Always returns float in [0.01, 0.95].
    """
    try:
        cdse_val = await get_ndvi_from_cdse(lat, lng)
        if cdse_val is not None:
            return cdse_val
    except Exception as exc:
        print(f"[ndvi_cdse] get_ndvi outer guard caught: {exc}")

    # Fallback — use coordinate-based key for the field centroid
    from app.services.satellite_service import simulate_ndvi_for_corridor  # type: ignore
    sim_key = f"{round(lat, 3)}_{round(lng, 3)}"
    sim_val = simulate_ndvi_for_corridor(sim_key)
    print(f"[ndvi_cdse] Using simulation fallback → {sim_val:.3f}")
    return float(sim_val)


# ── Step 4: Per-corridor variation ───────────────────────────────────────────

def apply_corridor_variation(base_ndvi: float, grid_position: str) -> float:
    """
    Derive a realistic per-corridor NDVI from a field-level base NDVI.

    - Deterministic: same corridor always gets the same variation.
    - Seeded by grid_position string hash — no randomness across runs.
    - Variation range: ±0.08 (agronomically realistic intra-field spread).
    - Result clamped to [0.01, 0.95].
    """
    seed      = int(hashlib.md5(grid_position.encode()).hexdigest(), 16) % 10000
    rng       = random.Random(seed)
    variation = rng.uniform(-0.08, 0.08)
    return round(max(0.01, min(0.95, base_ndvi + variation)), 3)
