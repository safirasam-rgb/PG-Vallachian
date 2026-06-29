from __future__ import annotations


class FlymetProvider:
    """Placeholder for future Flymet integration.

    Flymet is valuable because it is aviation/soaring oriented. It should not be
    scraped blindly until we confirm a stable and acceptable data route.

    Possible future modes:
    - manual input from Flymet map/meteogram values,
    - parsing known image URLs and metadata,
    - official Meteopress API if available,
    - user-provided exported data.
    """

    def fetch(self) -> None:
        raise NotImplementedError(
            "Flymet provider is not implemented yet. Use Open-Meteo provider first."
        )
