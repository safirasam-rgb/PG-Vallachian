from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


@dataclass(frozen=True)
class ForecastWindow:
    start_hour: int = 10
    end_hour: int = 17


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    latitude: float
    longitude: float
    elevation_m: float | None = None
    notes: str = ""


@dataclass(frozen=True)
class SectorSettings:
    allowed_spread_deg: float = 60.0
    ideal_spread_deg: float = 25.0
    ideal_wind_min_ms: float = 2.0
    ideal_wind_max_ms: float = 5.0
    strong_wind_ms: float = 8.0


@dataclass(frozen=True)
class AppConfig:
    timezone: str
    forecast_window: ForecastWindow
    locations: list[Location]
    sector_settings: SectorSettings
    raw: dict[str, Any]


def load_config(path: str | Path) -> AppConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    window = ForecastWindow(**data.get("forecast_window", {}))
    locations = [Location(**item) for item in data["locations"]]
    sector_settings = SectorSettings(**data.get("sector_settings", {}))

    return AppConfig(
        timezone=data.get("timezone", "Europe/Prague"),
        forecast_window=window,
        locations=locations,
        sector_settings=sector_settings,
        raw=data,
    )
