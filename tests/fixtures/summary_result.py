"""Small controlled result that conforms to the published summary schema."""

AREA_SUMMARY = {
    "bkn_indicators": {
        "low_vegetation_proxy_pct": 10.0,
        "medium_vegetation_proxy_pct": 5.0,
        "high_vegetation_proxy_pct": 2.0,
        "water_surface_pct": 20.0,
        "unpaved_surface_proxy_pct": 37.0,
    },
    "supporting_land_cover": {
        "unknown_vegetation_pct": 0.0,
        "road_pct": 30.0,
        "built_pct": 33.0,
        "bgt_explicitly_unpaved_pct": 1.0,
    },
}

SUMMARY_RESULT = {
    "process": {
        "name": "bgt-land-cover-summary",
        "algorithm_version": "test",
    },
    "source": {
        "name": "controlled PDOK test substitute",
        "retrieved_at": "2026-08-18T10:00:00+00:00",
        "collections": {},
        "feature_counts": {},
        "page_counts": {},
    },
    "input": {
        "latitude": 52.6324,
        "longitude": 4.7534,
        "inner_radius_m": 20,
        "outer_radius_m": 30,
    },
    "is_partial": False,
    "fetch_failures": {},
    "classification": {
        "is_official_standard": False,
        "method": "controlled test method",
        "unpaved_surface_definition": "controlled test definition",
        "unknown_vegetation_types": [],
        "overlap_priority": [],
    },
    "timing_seconds": {"by_collection": {}, "total": 0.1},
    "completed_at": "2026-08-18T10:00:01+00:00",
    "within_inner_radius": AREA_SUMMARY,
    "within_outer_radius": AREA_SUMMARY,
}
