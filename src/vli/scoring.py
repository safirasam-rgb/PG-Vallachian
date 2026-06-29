from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Any

from .config import ForecastWindow, Location, SectorSettings
from .math_utils import (
    angular_distance_deg,
    circular_mean_deg,
    clamp,
    safe_max,
    safe_mean,
    safe_sum,
)


SECTORS = {
    "S": 0,
    "SV": 45,
    "V": 90,
    "JV": 135,
    "J": 180,
    "JZ": 225,
    "Z": 270,
    "SZ": 315,
}


@dataclass(frozen=True)
class DaySlice:
    times: list[str]
    values: dict[str, list[Any]]


def select_day_window(data: dict[str, Any], target_date: date, window: ForecastWindow) -> DaySlice:
    hourly = data["hourly"]
    times = hourly["time"]

    indices: list[int] = []
    for i, time_string in enumerate(times):
        dt = datetime.fromisoformat(time_string)
        if dt.date() == target_date and window.start_hour <= dt.hour <= window.end_hour:
            indices.append(i)

    values = {
        key: [series[i] for i in indices]
        for key, series in hourly.items()
        if key != "time"
    }

    return DaySlice(times=[times[i] for i in indices], values=values)


def wind_stability_score(mean_wind_ms: float | None, max_gust_ms: float | None) -> int:
    if mean_wind_ms is None or max_gust_ms is None:
        return 0

    gust_delta = max(0.0, max_gust_ms - mean_wind_ms)

    if gust_delta <= 1.5:
        return 5
    if gust_delta <= 3.0:
        return 4
    if gust_delta <= 5.0:
        return 3
    if gust_delta <= 7.0:
        return 2
    return 1


def wind_strength_score(mean_wind_ms: float | None, settings: SectorSettings) -> float:
    if mean_wind_ms is None:
        return 0.0

    v = mean_wind_ms
    if settings.ideal_wind_min_ms <= v <= settings.ideal_wind_max_ms:
        return 100.0

    if v < settings.ideal_wind_min_ms:
        return clamp(20 + 80 * (v / max(settings.ideal_wind_min_ms, 0.1)))

    span = max(settings.strong_wind_ms - settings.ideal_wind_max_ms, 0.1)
    return clamp(100 - 70 * ((v - settings.ideal_wind_max_ms) / span), 0, 100)


def direction_score(global_direction_deg: float | None, sector_center_deg: float, settings: SectorSettings) -> float:
    if global_direction_deg is None:
        return 0.0

    dist = angular_distance_deg(global_direction_deg, sector_center_deg)

    if dist <= settings.ideal_spread_deg:
        return 100.0

    if dist >= settings.allowed_spread_deg:
        return 0.0

    usable_span = settings.allowed_spread_deg - settings.ideal_spread_deg
    return clamp(100 * (1 - (dist - settings.ideal_spread_deg) / usable_span))


def sector_scores(
    global_direction_deg: float | None,
    mean_wind_ms: float | None,
    stability: int,
    settings: SectorSettings,
) -> list[dict[str, Any]]:
    strength = wind_strength_score(mean_wind_ms, settings)

    result = []
    for name, center in SECTORS.items():
        d_score = direction_score(global_direction_deg, center, settings)
        score = 0.65 * d_score + 0.25 * strength + 0.10 * (stability * 20)
        result.append(
            {
                "sector": name,
                "center_deg": center,
                "score": round(clamp(score), 1),
                "direction_match": round(d_score, 1),
                "wind_strength_score": round(strength, 1),
            }
        )

    return sorted(result, key=lambda item: item["score"], reverse=True)


def cloud_score(mean_cloud: float | None) -> float:
    if mean_cloud is None:
        return 50.0

    if 20 <= mean_cloud <= 55:
        return 100.0
    if mean_cloud < 20:
        return clamp(70 + mean_cloud * 1.5)
    return clamp(100 - (mean_cloud - 55) * 1.7, 0, 100)


def thermal_score(day: DaySlice) -> dict[str, Any]:
    temp_max = safe_max(day.values.get("temperature_2m", []))
    radiation_max = safe_max(day.values.get("shortwave_radiation", []))
    cloud_mean = safe_mean(day.values.get("cloud_cover", []))
    precip_sum = safe_sum(day.values.get("precipitation", []))
    precip_prob_max = safe_max(day.values.get("precipitation_probability", []))

    temp_part = 0.0 if temp_max is None else clamp((temp_max - 12) / 20 * 100)
    rad_part = 50.0 if radiation_max is None else clamp(radiation_max / 700 * 100)
    cloud_part = cloud_score(cloud_mean)

    rain_penalty = min(35.0, precip_sum * 18)
    prob_penalty = 0.0 if precip_prob_max is None else max(0.0, precip_prob_max - 35) * 0.35

    score = 0.35 * temp_part + 0.35 * rad_part + 0.30 * cloud_part
    score -= rain_penalty + prob_penalty

    return {
        "score": round(clamp(score), 1),
        "max_temp_c": round(temp_max, 1) if temp_max is not None else None,
        "max_shortwave_wm2": round(radiation_max, 1) if radiation_max is not None else None,
        "mean_cloud_cover_pct": round(cloud_mean, 1) if cloud_mean is not None else None,
        "precip_sum_mm": round(precip_sum, 2),
        "precip_probability_max_pct": round(precip_prob_max, 1) if precip_prob_max is not None else None,
    }


def storm_note(day: DaySlice) -> dict[str, Any]:
    precip_prob_max = safe_max(day.values.get("precipitation_probability", []))
    showers_sum = safe_sum(day.values.get("showers", []))
    rain_sum = safe_sum(day.values.get("rain", []))

    risk = "nízké"
    if (precip_prob_max or 0) >= 55 or showers_sum >= 1.0:
        risk = "střední"
    if (precip_prob_max or 0) >= 75 or showers_sum >= 3.0:
        risk = "vyšší"

    return {
        "risk": risk,
        "precip_probability_max_pct": round(precip_prob_max, 1) if precip_prob_max is not None else None,
        "showers_sum_mm": round(showers_sum, 2),
        "rain_sum_mm": round(rain_sum, 2),
        "policy": "Bouřky nejsou automatický stop. Jsou samostatná riziková poznámka."
    }


def estimate_ceiling_potential(thermal: dict[str, Any], day: DaySlice) -> dict[str, Any]:
    low_cloud = safe_mean(day.values.get("cloud_cover_low", []))
    score = thermal["score"]
    if low_cloud is not None and low_cloud > 60:
        score -= 20

    label = "slabý"
    if score >= 70:
        label = "dobrý"
    elif score >= 50:
        label = "střední"

    return {
        "score": round(clamp(score), 1),
        "label": label,
        "confidence": "nízká až střední",
        "note": "Proxy odhad. Přesný dostup potřebuje sounding / thermal tops / usable lift."
    }


def compute_index(
    forecast_data: dict[str, Any],
    location: Location,
    target_date: date,
    window: ForecastWindow,
    settings: SectorSettings,
) -> dict[str, Any]:
    day = select_day_window(forecast_data, target_date, window)

    wind_mean = safe_mean(day.values.get("wind_speed_10m", []))
    gust_max = safe_max(day.values.get("wind_gusts_10m", []))
    direction = circular_mean_deg(day.values.get("wind_direction_10m", []))
    stability = wind_stability_score(wind_mean, gust_max)

    sectors = sector_scores(direction, wind_mean, stability, settings)
    thermal = thermal_score(day)
    storm = storm_note(day)
    ceiling = estimate_ceiling_potential(thermal, day)

    mean_cloud = safe_mean(day.values.get("cloud_cover", []))
    precip_sum = safe_sum(day.values.get("precipitation", []))

    wind_component = (
        0.45 * wind_strength_score(wind_mean, settings)
        + 0.35 * sectors[0]["direction_match"]
        + 0.20 * (stability * 20)
    )
    cloud_precip_component = cloud_score(mean_cloud) - min(35, precip_sum * 18)

    storm_penalty = 0
    if storm["risk"] == "střední":
        storm_penalty = 5
    elif storm["risk"] == "vyšší":
        storm_penalty = 10

    vli = (
        0.30 * wind_component
        + 0.30 * thermal["score"]
        + 0.20 * ceiling["score"]
        + 0.15 * cloud_precip_component
        + 0.05 * (stability * 20)
        - storm_penalty
    )

    verdict = make_verdict(vli, wind_mean, gust_max, thermal["score"], storm["risk"], sectors)
    issued_at = datetime.now().astimezone().isoformat(timespec="seconds")

    return {
        "schema_version": "0.1",
        "issued_at": issued_at,
        "target_date": target_date.isoformat(),
        "location": {
            "id": location.id,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "elevation_m": location.elevation_m,
        },
        "provider": forecast_data.get("_meta", {}),
        "forecast_window": {
            "start_hour": window.start_hour,
            "end_hour": window.end_hour,
            "sample_count": len(day.times),
            "times": day.times,
        },
        "global": {
            "direction_deg": round(direction, 0) if direction is not None else None,
            "mean_wind_ms": round(wind_mean, 1) if wind_mean is not None else None,
            "max_gust_ms": round(gust_max, 1) if gust_max is not None else None,
            "stability_1to5": stability,
        },
        "sector_scores": sectors,
        "scores": {
            "vli": round(clamp(vli), 1),
            "wind_component": round(clamp(wind_component), 1),
            "thermal": thermal,
            "ceiling": ceiling,
            "cloud_precip_component": round(clamp(cloud_precip_component), 1),
        },
        "risks": {"storm": storm},
        "verdict": verdict,
    }


def make_verdict(
    vli: float,
    wind_mean: float | None,
    gust_max: float | None,
    thermal: float,
    storm_risk: str,
    sectors: list[dict[str, Any]],
) -> str:
    best = sectors[0]["sector"] if sectors else "?"
    v = wind_mean or 0

    if vli >= 75:
        base = "Velmi dobrý letový den."
    elif vli >= 60:
        base = "Letově zajímavý den."
    elif vli >= 45:
        base = "Použitelný, ale selektivní den."
    else:
        base = "Slabý nebo problémový den."

    if thermal >= 70 and v < 2.5:
        detail = "Termika může fungovat, ale start bude hodně záviset na lokálním nádechu svahu."
    elif thermal >= 70:
        detail = "Termický potenciál je dobrý."
    elif thermal >= 50:
        detail = "Termika spíš střední, nečekal bych zázraky."
    else:
        detail = "Termický potenciál je slabý."

    storm = ""
    if storm_risk in {"střední", "vyšší"}:
        storm = f" Bouřkové/přeháňkové riziko: {storm_risk}; sledovat vývoj, radar a únikové varianty."

    return f"{base} Nejlepší směrový sektor: {best}. {detail}{storm}"
