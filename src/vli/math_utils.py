from __future__ import annotations

import math
from statistics import mean


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def angular_distance_deg(a: float, b: float) -> float:
    """Smallest distance between two bearings in degrees."""
    return abs((a - b + 180) % 360 - 180)


def circular_mean_deg(values: list[float]) -> float | None:
    """Vector average for wind directions.

    Wind direction is kept as meteorological direction: degrees FROM which it blows.
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return None

    sin_sum = sum(math.sin(math.radians(v)) for v in vals)
    cos_sum = sum(math.cos(math.radians(v)) for v in vals)

    if abs(sin_sum) < 1e-9 and abs(cos_sum) < 1e-9:
        return None

    return (math.degrees(math.atan2(sin_sum, cos_sum)) + 360) % 360


def safe_mean(values: list[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return mean(vals) if vals else None


def safe_max(values: list[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return max(vals) if vals else None


def safe_sum(values: list[float | None]) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) if vals else 0.0
