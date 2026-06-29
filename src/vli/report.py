from __future__ import annotations

from typing import Any


def format_deg(value: float | int | None) -> str:
    return "?" if value is None else f"{value:.0f}°"


def format_ms(value: float | int | None) -> str:
    return "?" if value is None else f"{value:.1f}"


def top_sector_lines(result: dict[str, Any], count: int = 8) -> list[str]:
    g = result["global"]
    direction = format_deg(g["direction_deg"])
    mean_wind = format_ms(g["mean_wind_ms"])
    gust = format_ms(g["max_gust_ms"])
    stability = g["stability_1to5"]

    lines = []
    for sector in result["sector_scores"][:count]:
        lines.append(
            f"- **{sector['sector']} starty:** {sector['score']:.0f}/100 — "
            f"{direction} — {mean_wind}/{gust} m/s — stabilita {stability}/5"
        )
    return lines


def render_markdown(result: dict[str, Any]) -> str:
    g = result["global"]
    scores = result["scores"]
    thermal = scores["thermal"]
    ceiling = scores["ceiling"]
    storm = result["risks"]["storm"]

    lines: list[str] = []
    lines.append(f"# Valašský PG index — {result['location']['name']} — {result['target_date']}")
    lines.append("")
    lines.append(f"**Celkem: {scores['vli']:.0f}/100**")
    lines.append("")
    lines.append(result["verdict"])
    lines.append("")
    lines.append("## Globál")
    lines.append("")
    lines.append(
        f"- Směr: **{format_deg(g['direction_deg'])}**\n"
        f"- Vítr: **{format_ms(g['mean_wind_ms'])}/{format_ms(g['max_gust_ms'])} m/s**\n"
        f"- Stabilita: **{g['stability_1to5']}/5**\n"
        f"- Okno: **{result['forecast_window']['start_hour']}:00–{result['forecast_window']['end_hour']}:00**"
    )
    lines.append("")
    lines.append("## Směrové sektory")
    lines.append("")
    lines.extend(top_sector_lines(result))
    lines.append("")
    lines.append("## Termika")
    lines.append("")
    lines.append(
        f"- Skóre: **{thermal['score']:.0f}/100**\n"
        f"- Max. teplota: **{thermal['max_temp_c']} °C**\n"
        f"- Max. krátkovlnné záření: **{thermal['max_shortwave_wm2']} W/m²**\n"
        f"- Průměrná oblačnost: **{thermal['mean_cloud_cover_pct']} %**\n"
        f"- Srážky v okně: **{thermal['precip_sum_mm']} mm**\n"
        f"- Max. pravděpodobnost srážek: **{thermal['precip_probability_max_pct']} %**"
    )
    lines.append("")
    lines.append("## Dostup / použitelné stoupání")
    lines.append("")
    lines.append(
        f"- Skóre: **{ceiling['score']:.0f}/100**\n"
        f"- Očekávaný dostup: **{ceiling.get('estimated_ceiling_m', '?')} m**\n"
        f"- Slovně: **{ceiling['label']}**\n"
        f"- Jistota: **{ceiling['confidence']}**\n"
        f"- Poznámka: {ceiling['note']}"
    )
    lines.append("")
    lines.append("## Rizika")
    lines.append("")
    lines.append(
        f"- Bouřky/přeháňky: **{storm['risk']}**\n"
        f"- Max. pravděpodobnost srážek: **{storm['precip_probability_max_pct']} %**\n"
        f"- Přeháňky: **{storm['showers_sum_mm']} mm**\n"
        f"- Déšť: **{storm['rain_sum_mm']} mm**\n"
        f"- Politika indexu: {storm['policy']}"
    )
    lines.append("")
    lines.append("## Poznámka")
    lines.append("")
    lines.append(
        "Tento report je lokální rozhodovací pomůcka, ne bezpečnostní autorita. "
        "Ranní realita, radar, obloha, vývoj kumulů a vlastní úsudek mají přednost."
    )
    lines.append("")
    return "\n".join(lines)
