"""Application-defined mappings from BGT features to summary categories."""

VEGETATION_TYPES_BY_CATEGORY = {
    "lage vegetatie": {
        "heide",
        "duin",
        "grasland overig",
        "rietland",
        "kwelder",
        "bouwland",
        "grasland agrarisch",
        "groenvoorziening: planten",
        "groenvoorziening: struikrozen",
        "groenvoorziening: heesters",
        "groenvoorziening: bodembedekkers",
        "groenvoorziening: gras- en kruidachtigen",
        "transitie",
    },
    "middelhoge vegetatie": {
        "struiken",
        "fruitteelt",
        "fruitteelt: laagstam boomgaarden",
        "fruitteelt: wijngaarden",
        "fruitteelt: klein fruit",
        "boomteelt",
        "groenvoorziening",
    },
    "hoge vegetatie": {
        "gemengd bos",
        "naaldbos",
        "loofbos",
        "houtwal",
        "loofbos: griend en hakhout",
        "moeras",
        "fruitteelt: hoogstam boomgaarden",
        "groenvoorziening: bosplantsoen",
    },
}

CATEGORY_TO_COLUMN = {
    "lage vegetatie": "oppervlak_lage_vegetatie_pct",
    "middelhoge vegetatie": "oppervlak_middelhoge_vegetatie_pct",
    "hoge vegetatie": "oppervlak_hoge_vegetatie_pct",
    "onbekende vegetatie": "onbekende_vegetatie_pct",
    "bebouwd gebied": "oppervlak_bebouwd_pct",
    "water": "oppervlak_water_pct",
    "weg": "oppervlak_wegen_pct",
    "pand": "oppervlak_panden_pct",
    "onverhard": "oppervlak_onverhard_pct",
}

EXPLICITLY_UNPAVED_TYPES = {"onverhard", "zand"}

# These Dutch category identifiers drive the current masking calculation.
OVERLAP_PRIORITY = ["pand", "weg", "bebouwd gebied", "hoge vegetatie", "middelhoge vegetatie"]

BKN_UNPAVED_CATEGORIES = {
    "lage vegetatie",
    "middelhoge vegetatie",
    "hoge vegetatie",
    "onbekende vegetatie",
    "water",
    "onverhard",
}


def vegetation_category(type_value: str) -> str | None:
    """Return the application category for one BGT vegetation type."""
    for category, types in VEGETATION_TYPES_BY_CATEGORY.items():
        if type_value in types:
            return category
    return None


def feature_category(collection: str, properties: dict) -> tuple[str, str | None]:
    """Classify one feature and return any unknown vegetation label."""
    if collection == "begroeid":
        physical_appearance = properties.get("fysiek_voorkomen", "")
        detailed_appearance = properties.get("plus_fysiek_voorkomen", "")
        type_value = f"{physical_appearance}: {detailed_appearance}" if detailed_appearance else physical_appearance
        category = vegetation_category(type_value)
        if category is None:
            return "onbekende vegetatie", type_value or "<empty>"
        return category, None

    if collection == "onbegroeid":
        physical_appearance = properties.get("fysiek_voorkomen", "")
        category = "onverhard" if physical_appearance in EXPLICITLY_UNPAVED_TYPES else "bebouwd gebied"
        return category, None

    return collection, None


def summarize_percentages(
    percentages: dict[str, float],
    built_percentage: float,
    bkn_unpaved_percentage: float,
) -> dict:
    """Assemble the stable public percentage result for one analysis radius."""
    return {
        "bkn_indicators": {
            "low_vegetation_proxy_pct": round(percentages.get("lage vegetatie", 0), 2),
            "medium_vegetation_proxy_pct": round(percentages.get("middelhoge vegetatie", 0), 2),
            "high_vegetation_proxy_pct": round(percentages.get("hoge vegetatie", 0), 2),
            "water_surface_pct": round(percentages.get("water", 0), 2),
            "unpaved_surface_proxy_pct": round(bkn_unpaved_percentage, 2),
        },
        "supporting_land_cover": {
            "unknown_vegetation_pct": round(percentages.get("onbekende vegetatie", 0), 2),
            "road_pct": round(percentages.get("weg", 0), 2),
            "built_pct": round(built_percentage, 2),
            "bgt_explicitly_unpaved_pct": round(percentages.get("onverhard", 0), 2),
        },
    }
