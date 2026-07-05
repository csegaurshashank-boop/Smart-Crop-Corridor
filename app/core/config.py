import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "crop_corridor"
    SECRET_KEY: str = "changeme_super_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── AI Pipeline: Copernicus Data Space Ecosystem (CDSE) ──────────────────
    # FREE real Sentinel-2 NDVI — register at https://dataspace.copernicus.eu
    CDSE_CLIENT_ID: Optional[str] = ""
    CDSE_CLIENT_SECRET: Optional[str] = ""

    # ── Optional legacy keys (not required for system to run) ────────────────
    SENTINEL_HUB_TOKEN: Optional[str] = ""
    OPENWEATHER_API_KEY: Optional[str] = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()