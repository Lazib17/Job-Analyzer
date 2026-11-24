"""Match a scraped job location to a chosen Japanese city."""

from typing import Optional

# Aliases include the city, its prefecture, and the English names boards actually store.
CITIES: dict[str, tuple[str, ...]] = {
    "Tokyo": ("tokyo", "東京"),
    "Osaka": ("osaka", "大阪"),
    "Yokohama": ("yokohama", "横浜", "kanagawa", "神奈川"),
    "Nagoya": ("nagoya", "名古屋", "aichi", "愛知"),
    "Fukuoka": ("fukuoka", "福岡"),
    "Sapporo": ("sapporo", "札幌", "hokkaido", "北海道"),
    "Kobe": ("kobe", "神戸", "hyogo", "兵庫"),
    "Kyoto": ("kyoto", "京都"),
    "Hiroshima": ("hiroshima", "広島"),
    "Sendai": ("sendai", "仙台", "miyagi", "宮城"),
}

CITY_NAMES = ("Any", *CITIES)


def city_fits(location: Optional[str], city: str) -> bool:
    """Keep every listing when the city is Any. Otherwise require a city or prefecture match."""
    choice = (city or "Any").strip()
    if choice == "Any":
        return True
    tokens = CITIES.get(choice)
    if not tokens:
        return True
    text = location or ""
    lowered = text.lower()
    # 東京都 contains the characters 京都, so a Kyoto search must not treat Tokyo as Kyoto.
    if choice == "Kyoto" and ("東京都" in text or "tokyo" in lowered):
        return "kyoto" in lowered or "京都府" in text
    return any(token in lowered or token in text for token in tokens)
