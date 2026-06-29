from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
import requests


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Conservative variables that should work in the standard Forecast API.
HOURLY_BASE = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "rain",
    "showers",
    "weather_code",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "shortwave_radiation",
]

# Optional. Some model combinations may reject pressure-level variables.
PRESSURE_LEVELS = [
    "wind_speed_850hPa",
    "wind_direction_850hPa",
    "temperature_850hPa",
    "geopotential_height_850hPa",
    "wind_speed_700hPa",
    "wind_direction_700hPa",
    "temperature_700hPa",
    "geopotential_height_700hPa",
]


@dataclass(frozen=True)
class OpenMeteoRequest:
    latitude: float
    longitude: float
    timezone: str = "Europe/Prague"
    include_pressure_levels: bool = False


def _request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"Open-Meteo request failed: {response.status_code} {response.text[:500]}") from exc
    return response.json()


def fetch_forecast(req: OpenMeteoRequest, forecast_days: int = 2) -> dict[str, Any]:
    hourly = list(HOURLY_BASE)
    if req.include_pressure_levels:
        hourly.extend(PRESSURE_LEVELS)

    params = {
        "latitude": req.latitude,
        "longitude": req.longitude,
        "timezone": req.timezone,
        "forecast_days": forecast_days,
        "hourly": ",".join(hourly),
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
    }

    warnings: list[str] = []
    try:
        data = _request_json(FORECAST_URL, params)
    except RuntimeError:
        # Fallback: use only base variables. This keeps the morning automation alive.
        warnings.append("pressure_level_variables_failed_or_unavailable")
        params["hourly"] = ",".join(HOURLY_BASE)
        data = _request_json(FORECAST_URL, params)

    data.setdefault("_meta", {})
    data["_meta"]["provider"] = "open-meteo"
    data["_meta"]["warnings"] = warnings
    data["_meta"]["requested_pressure_levels"] = req.include_pressure_levels
    return data


def fetch_historical_actual(req: OpenMeteoRequest, target_date: date) -> dict[str, Any]:
    """Fetch historical/reanalysis-like actual weather for validation.

    This is not the same as a pilot-observed day. It is good enough to verify
    whether wind/temperature/cloud/rain roughly matched the morning forecast.
    """
    params = {
        "latitude": req.latitude,
        "longitude": req.longitude,
        "timezone": req.timezone,
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "hourly": ",".join(HOURLY_BASE),
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
    }
    data = _request_json(HISTORICAL_URL, params)
    data.setdefault("_meta", {})
    data["_meta"]["provider"] = "open-meteo-historical"
    return data
