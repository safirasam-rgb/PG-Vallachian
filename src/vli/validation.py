from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .config import ForecastWindow
from .math_utils import circular_mean_deg, safe_max, safe_mean, safe_sum
from .scoring import select_day_window


def summarize_actual(actual_data: dict[str, Any], target_date: date, window: ForecastWindow) -> dict[str, Any]:
    day = select_day_window(actual_data, target_date, window)

    return {
        "target_date": target_date.isoformat(),
        "validated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "forecast_window": {
            "start_hour": window.start_hour,
            "end_hour": window.end_hour,
            "sample_count": len(day.times),
            "times": day.times,
        },
        "global": {
            "direction_deg": _round(circular_mean_deg(day.values.get("wind_direction_10m", [])), 0),
            "mean_wind_ms": _round(safe_mean(day.values.get("wind_speed_10m", [])), 1),
            "max_gust_ms": _round(safe_max(day.values.get("wind_gusts_10m", [])), 1),
        },
        "weather": {
            "max_temp_c": _round(safe_max(day.values.get("temperature_2m", [])), 1),
            "mean_cloud_cover_pct": _round(safe_mean(day.values.get("cloud_cover", [])), 1),
            "precip_sum_mm": round(safe_sum(day.values.get("precipitation", [])), 2),
            "precip_probability_max_pct": _round(safe_max(day.values.get("precipitation_probability", [])), 1),
        },
    }


def compare_forecast_to_actual(forecast: dict[str, Any], actual_summary: dict[str, Any]) -> dict[str, Any]:
    forecast_global = forecast.get("global", {})
    forecast_thermal = forecast.get("scores", {}).get("thermal", {})
    actual_global = actual_summary.get("global", {})
    actual_weather = actual_summary.get("weather", {})

    return {
        "target_date": forecast.get("target_date") or actual_summary.get("target_date"),
        "location": forecast.get("location", {}),
        "validated_at": actual_summary.get("validated_at"),
        "forecast": {
            "direction_deg": forecast_global.get("direction_deg"),
            "mean_wind_ms": forecast_global.get("mean_wind_ms"),
            "max_gust_ms": forecast_global.get("max_gust_ms"),
            "max_temp_c": forecast_thermal.get("max_temp_c"),
            "mean_cloud_cover_pct": forecast_thermal.get("mean_cloud_cover_pct"),
            "precip_sum_mm": forecast_thermal.get("precip_sum_mm"),
            "precip_probability_max_pct": forecast_thermal.get("precip_probability_max_pct"),
            "vli": forecast.get("scores", {}).get("vli"),
        },
        "actual": {
            "direction_deg": actual_global.get("direction_deg"),
            "mean_wind_ms": actual_global.get("mean_wind_ms"),
            "max_gust_ms": actual_global.get("max_gust_ms"),
            "max_temp_c": actual_weather.get("max_temp_c"),
            "mean_cloud_cover_pct": actual_weather.get("mean_cloud_cover_pct"),
            "precip_sum_mm": actual_weather.get("precip_sum_mm"),
            "precip_probability_max_pct": actual_weather.get("precip_probability_max_pct"),
        },
        "deltas": {
            "direction_deg": _direction_delta(forecast_global.get("direction_deg"), actual_global.get("direction_deg")),
            "mean_wind_ms": _delta(forecast_global.get("mean_wind_ms"), actual_global.get("mean_wind_ms")),
            "max_gust_ms": _delta(forecast_global.get("max_gust_ms"), actual_global.get("max_gust_ms")),
            "max_temp_c": _delta(forecast_thermal.get("max_temp_c"), actual_weather.get("max_temp_c")),
            "mean_cloud_cover_pct": _delta(
                forecast_thermal.get("mean_cloud_cover_pct"),
                actual_weather.get("mean_cloud_cover_pct"),
            ),
            "precip_sum_mm": _delta(forecast_thermal.get("precip_sum_mm"), actual_weather.get("precip_sum_mm")),
            "precip_probability_max_pct": _delta(
                forecast_thermal.get("precip_probability_max_pct"),
                actual_weather.get("precip_probability_max_pct"),
            ),
        },
    }


def render_validation_markdown(result: dict[str, Any]) -> str:
    location = result.get("location", {})
    forecast = result.get("forecast", {})
    actual = result.get("actual", {})
    deltas = result.get("deltas", {})

    lines = [
        f"# Validace PG indexu - {location.get('name', '?')} - {result.get('target_date', '?')}",
        "",
        f"Validovano: {result.get('validated_at', '?')}",
        "",
        "| Velicina | Predpoved | Realita | Rozdil |",
        "| --- | ---: | ---: | ---: |",
        _row("Smer vetru", _deg(forecast.get("direction_deg")), _deg(actual.get("direction_deg")), _deg(deltas.get("direction_deg"))),
        _row("Prumerny vitr", _ms(forecast.get("mean_wind_ms")), _ms(actual.get("mean_wind_ms")), _ms(deltas.get("mean_wind_ms"))),
        _row("Narazy", _ms(forecast.get("max_gust_ms")), _ms(actual.get("max_gust_ms")), _ms(deltas.get("max_gust_ms"))),
        _row("Max. teplota", _unit(forecast.get("max_temp_c"), "C"), _unit(actual.get("max_temp_c"), "C"), _unit(deltas.get("max_temp_c"), "C")),
        _row("Oblacnost", _pct(forecast.get("mean_cloud_cover_pct")), _pct(actual.get("mean_cloud_cover_pct")), _pct(deltas.get("mean_cloud_cover_pct"))),
        _row("Srazky", _unit(forecast.get("precip_sum_mm"), "mm"), _unit(actual.get("precip_sum_mm"), "mm"), _unit(deltas.get("precip_sum_mm"), "mm")),
        _row("Pravd. srazek", _pct(forecast.get("precip_probability_max_pct")), _pct(actual.get("precip_probability_max_pct")), _pct(deltas.get("precip_probability_max_pct"))),
        "",
    ]
    return "\n".join(lines)


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def _delta(forecast_value: float | int | None, actual_value: float | int | None) -> float | None:
    if forecast_value is None or actual_value is None:
        return None
    return round(float(actual_value) - float(forecast_value), 1)


def _direction_delta(forecast_value: float | int | None, actual_value: float | int | None) -> float | None:
    if forecast_value is None or actual_value is None:
        return None
    return round(abs((float(actual_value) - float(forecast_value) + 180) % 360 - 180), 0)


def _deg(value: float | int | None) -> str:
    return "?" if value is None else f"{value:.0f} deg"


def _ms(value: float | int | None) -> str:
    return "?" if value is None else f"{value:.1f} m/s"


def _pct(value: float | int | None) -> str:
    return "?" if value is None else f"{value:.1f} %"


def _unit(value: float | int | None, unit: str) -> str:
    return "?" if value is None else f"{value:.1f} {unit}"


def _row(label: str, forecast: str, actual: str, delta: str) -> str:
    return f"| {label} | {forecast} | {actual} | {delta} |"
