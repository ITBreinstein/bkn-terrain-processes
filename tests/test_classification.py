"""Tests for the application-defined BGT classification rules."""

from bkn_terrain_processes.classification import feature_category, summarize_percentages


def test_classifies_known_and_unknown_vegetation_types():
    assert feature_category("begroeid", {"fysiek_voorkomen": "loofbos"}) == ("hoge vegetatie", None)
    assert feature_category(
        "begroeid",
        {
            "fysiek_voorkomen": "groenvoorziening",
            "plus_fysiek_voorkomen": "struikrozen",
        },
    ) == ("lage vegetatie", None)
    assert feature_category("begroeid", {"fysiek_voorkomen": "nieuw type"}) == (
        "onbekende vegetatie",
        "nieuw type",
    )


def test_classifies_explicitly_unpaved_and_other_unvegetated_terrain():
    assert feature_category("onbegroeid", {"fysiek_voorkomen": "zand"}) == ("onverhard", None)
    assert feature_category("onbegroeid", {"fysiek_voorkomen": "erf"}) == ("bebouwd gebied", None)


def test_summary_keeps_the_public_field_names_and_rounding():
    summary = summarize_percentages(
        {
            "lage vegetatie": 10.126,
            "middelhoge vegetatie": 20.234,
            "hoge vegetatie": 30.345,
            "water": 4.444,
            "onbekende vegetatie": 2.345,
            "weg": 3.456,
            "onverhard": 5.678,
        },
        built_percentage=12.345,
        bkn_unpaved_percentage=72.222,
    )

    assert summary == {
        "bkn_indicators": {
            "low_vegetation_proxy_pct": 10.13,
            "medium_vegetation_proxy_pct": 20.23,
            "high_vegetation_proxy_pct": 30.34,
            "water_surface_pct": 4.44,
            "unpaved_surface_proxy_pct": 72.22,
        },
        "supporting_land_cover": {
            "unknown_vegetation_pct": 2.35,
            "road_pct": 3.46,
            "built_pct": 12.35,
            "bgt_explicitly_unpaved_pct": 5.68,
        },
    }
