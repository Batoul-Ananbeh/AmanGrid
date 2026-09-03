import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = "AmanGrid API"
    app_version: str = "0.1.0"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw_origins = os.getenv("AMANGRID_CORS_ORIGINS", "http://localhost:5173")
    origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
    return Settings(cors_origins=origins or Settings.cors_origins)
