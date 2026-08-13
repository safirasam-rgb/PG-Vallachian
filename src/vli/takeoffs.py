from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .math_utils import angular_distance_deg


@dataclass(frozen=True)
class Takeoff:
    name: str
    wind_from_deg: float
    wind_to_deg: float
    distance_km: float


def load_takeoffs(path: str | Path) -> list[Takeoff]:
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    return [
        Takeoff(
            name=str(item["name"]),
            wind_from_deg=float(item["wind_from_deg"]),
            wind_to_deg=float(item["wind_to_deg"]),
            distance_km=float(item["distance_km"]),
        )
        for item in raw
    ]


def recommend_takeoffs(wind_direction_deg: float | int | None, takeoffs: list[Takeoff]) -> list[dict[str, Any]]:
    if wind_direction_deg is None:
        return []

    result: list[dict[str, Any]] = []
    for takeoff in takeoffs:
        fit = _fit_ratio(float(wind_direction_deg), takeoff.wind_from_deg, takeoff.wind_to_deg)
        if fit > 1.1:
            continue

        if fit <= 0.5:
            quality = "green"
            quality_label = "ideal"
            quality_rank = 0
        elif fit <= 0.9:
            quality = "yellow"
            quality_label = "okraj"
            quality_rank = 1
        else:
            quality = "red"
            quality_label = "hranicni"
            quality_rank = 2

        result.append(
            {
                "name": takeoff.name,
                "wind_from_deg": int(round(takeoff.wind_from_deg)),
                "wind_to_deg": int(round(takeoff.wind_to_deg)),
                "distance_km": int(round(takeoff.distance_km)),
                "quality": quality,
                "quality_label": quality_label,
                "fit_ratio": round(fit, 2),
                "center_delta_deg": round(_center_delta(float(wind_direction_deg), takeoff), 0),
                "_quality_rank": quality_rank,
            }
        )

    result.sort(key=lambda item: (item["distance_km"], item["_quality_rank"], item["center_delta_deg"], item["name"]))
    for item in result:
        item.pop("_quality_rank", None)
    return result


def _range_width(start: float, end: float) -> float:
    width = (end - start) % 360
    return 360.0 if width == 0 else width


def _range_center(start: float, end: float) -> float:
    width = _range_width(start, end)
    return (start + width / 2) % 360


def _fit_ratio(direction: float, start: float, end: float) -> float:
    half_width = max(_range_width(start, end) / 2, 1)
    center = _range_center(start, end)
    return angular_distance_deg(direction, center) / half_width


def _center_delta(direction: float, takeoff: Takeoff) -> float:
    center = _range_center(takeoff.wind_from_deg, takeoff.wind_to_deg)
    return angular_distance_deg(direction, center)
