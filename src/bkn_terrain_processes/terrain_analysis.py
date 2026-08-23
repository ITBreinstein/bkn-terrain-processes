"""Coordinate a nationwide BGT land-cover summary for one location.

The imported classification is an application-defined interpretation of BGT
physical appearances, not an official BGT or OGC classification standard.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter

import requests
from requests import RequestException
from shapely.geometry import shape

from .classification import (
    CATEGORY_TO_COLUMN,
    OVERLAP_PRIORITY,
    feature_category,
    summarize_percentages,
)
from .geometry import (
    build_analysis_buffers,
    category_percentages,
    clip_feature_to_buffer,
    mask_category_geometries,
    merge_category_geometries,
    to_rd_geometry,
    unpaved_surface_percentage,
)
from .pdok import BGT_COLLECTION_URLS, fetch_features_paginated

logger = logging.getLogger(__name__)

ALGORITHM_VERSION = "0.2.0"
SOURCE_NAME = "PDOK BGT OGC API Features"

# Progress is reported as a percentage of the whole calculation. It stops
# below 95 because the caller still has to store the result: pygeoapi's job
# manager uses 95 for "writing job output" and 100 for "job complete".
PROGRESS_FETCH_START = 10
PROGRESS_FETCH_COMPLETE = 65
PROGRESS_CLASSIFIED = 75
PROGRESS_MERGED = 85
PROGRESS_SUMMARISED = 92

ProgressCallback = Callable[[int, str], None]


def _report_progress(on_progress: ProgressCallback | None, percent: int, message: str) -> None:
    """
    Report calculation progress, if the caller asked for it.

    A caller's callback typically writes to shared job state, so it can fail
    for reasons that have nothing to do with the calculation. Such a failure
    must never lose work that has already been done.

    :param on_progress: optional caller-supplied progress callback
    :param percent: percentage of the whole calculation completed
    :param message: human-readable description of the current phase
    """

    if on_progress is None:
        return

    try:
        on_progress(percent, message)
    except Exception:
        logger.warning("Progress callback failed at %s%%; continuing calculation", percent, exc_info=True)


def get_terrain_analysis_nl(
    lat: float,
    lon: float,
    inner_radius_m: int = 300,
    outer_radius_m: int = 500,
    limit: int = 1000,
    on_progress: ProgressCallback | None = None,
):
    """
    Fetch and analyze terrain data around a given lat/lon point.

    Args:
        lat: Latitude of the center point
        lon: Longitude of the center point
        inner_radius_m: Inner analysis radius in metres
        outer_radius_m: Outer analysis radius in metres
        limit: Maximum number of features to fetch per API request
        on_progress: Optional callback receiving (percent, message) as the
            calculation advances. Synchronous callers can ignore it;
            asynchronous execution uses it to publish job progress. It is
            called from the calling thread and must return quickly.

    Returns:
        Dictionary with terrain percentages and counts
    """

    try:
        lat = float(lat)
        lon = float(lon)
        buffer_300m = int(inner_radius_m)
        buffer_500m = int(outer_radius_m)
        limit = int(limit)
    except (TypeError, ValueError) as err:
        raise ValueError("Coordinates, buffer radii and limit must be numeric") from err

    if not -90 <= lat <= 90:
        raise ValueError("lat must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("lon must be between -180 and 180")
    if buffer_300m <= 0 or buffer_500m <= 0:
        raise ValueError("Buffer radii must be positive")
    if buffer_300m > buffer_500m:
        raise ValueError("inner_radius_m cannot be larger than outer_radius_m")

    started_at = datetime.now(UTC)
    total_started = perf_counter()
    if limit <= 0:
        raise ValueError("limit must be positive")

    buffers = build_analysis_buffers(lon, lat, buffer_300m, buffer_500m)
    buffer_area_500m = buffers.outer_rd.area
    buffer_area_300m = buffers.inner_rd.area
    bminx, bminy, bmaxx, bmaxy = buffers.outer_wgs_bounds

    features_dict = {}
    source_timings_seconds = {}
    source_page_counts = {}

    fetch_failures = {}

    collection_count = len(BGT_COLLECTION_URLS)
    fetch_progress_span = PROGRESS_FETCH_COMPLETE - PROGRESS_FETCH_START
    _report_progress(on_progress, PROGRESS_FETCH_START, f"retrieving {collection_count} BGT collections")

    with requests.Session() as session:
        for collections_done, (key, url) in enumerate(BGT_COLLECTION_URLS.items(), start=1):
            source_started = perf_counter()
            features_dict[key] = []

            try:
                features, page_count = fetch_features_paginated(
                    url,
                    (bminx, bminy, bmaxx, bmaxy),
                    limit,
                    started_at,
                    session,
                )
                features_dict[key] = features
                source_page_counts[key] = page_count

            except RequestException as e:
                logger.warning("HTTP error while fetching %s features: %s", key, e)
                fetch_failures[key] = f"http_error: {e}"

            except ValueError as e:
                logger.warning("JSON/parse error while fetching %s features: %s", key, e)
                fetch_failures[key] = f"parse_error: {e}"

            source_timings_seconds[key] = round(perf_counter() - source_started, 3)
            _report_progress(
                on_progress,
                PROGRESS_FETCH_START + round(fetch_progress_span * collections_done / collection_count),
                f"retrieved BGT collection {key} ({collections_done}/{collection_count})",
            )

    feature_count = sum(len(features) for features in features_dict.values())
    if feature_count == 0:
        if fetch_failures:
            failed_sources = ", ".join(sorted(fetch_failures))
            raise RuntimeError(f"No terrain data could be retrieved; failed PDOK sources: {failed_sources}")
        raise LookupError("No PDOK BGT terrain features were found around this coordinate")

    seen_geometries = set()

    category_geometries_500m = {category: [] for category in CATEGORY_TO_COLUMN}
    category_geometries_300m = {category: [] for category in CATEGORY_TO_COLUMN}

    feature_warning_count = {}
    feature_warning_limit = 5
    unknown_vegetation_types = set()

    def log_limited_warning(key: str, message: str):
        feature_warning_count[key] = feature_warning_count.get(key, 0) + 1
        if feature_warning_count[key] <= feature_warning_limit:
            logger.warning(message)
        elif feature_warning_count[key] == feature_warning_limit + 1:
            logger.warning("Further warnings of type '%s' will be suppressed", key)

    # Process vegetated areas
    for feature in features_dict.get("begroeid", []):
        try:
            geom = shape(feature["geometry"])
            geom_wkt = geom.wkt

            if geom_wkt not in seen_geometries:
                seen_geometries.add(geom_wkt)
                clipped_geom_500m = clip_feature_to_buffer(geom, buffers.outer_rd)
                clipped_geom_300m = clip_feature_to_buffer(geom, buffers.inner_rd)

                if clipped_geom_500m or clipped_geom_300m:
                    props = feature["properties"]
                    category, unknown_type = feature_category("begroeid", props)
                    if unknown_type is not None:
                        unknown_vegetation_types.add(unknown_type)

                    if clipped_geom_500m:
                        geom_rd_500m = to_rd_geometry(clipped_geom_500m)
                        category_geometries_500m[category].append(geom_rd_500m)
                    if clipped_geom_300m:
                        geom_rd_300m = to_rd_geometry(clipped_geom_300m)
                        category_geometries_300m[category].append(geom_rd_300m)

        except Exception as e:
            log_limited_warning("begroeid_process", f"Failed to process begroeid feature: {e}")

    # Process onbegroeid: split onverhard/zand vs rest (bebouwd gebied)
    for feature in features_dict.get("onbegroeid", []):
        try:
            geom = shape(feature["geometry"])
            geom_wkt = geom.wkt

            if geom_wkt not in seen_geometries:
                seen_geometries.add(geom_wkt)
                clipped_geom_500m = clip_feature_to_buffer(geom, buffers.outer_rd)
                clipped_geom_300m = clip_feature_to_buffer(geom, buffers.inner_rd)

                if clipped_geom_500m or clipped_geom_300m:
                    category, _ = feature_category("onbegroeid", feature["properties"])

                    if clipped_geom_500m:
                        category_geometries_500m[category].append(to_rd_geometry(clipped_geom_500m))
                    if clipped_geom_300m:
                        category_geometries_300m[category].append(to_rd_geometry(clipped_geom_300m))

        except Exception as e:
            log_limited_warning("onbegroeid_process", f"Failed to process onbegroeid feature: {e}")

    # Process other categories
    for api_key, features in features_dict.items():
        if api_key in ["begroeid", "onbegroeid"]:
            continue

        category, _ = feature_category(api_key, {})
        if category not in category_geometries_500m:
            continue

        for feature in features:
            try:
                geom = shape(feature["geometry"])
                geom_wkt = geom.wkt

                if geom_wkt not in seen_geometries:
                    seen_geometries.add(geom_wkt)
                    clipped_geom_500m = clip_feature_to_buffer(geom, buffers.outer_rd)
                    clipped_geom_300m = clip_feature_to_buffer(geom, buffers.inner_rd)

                    if clipped_geom_500m:
                        geom_rd_500m = to_rd_geometry(clipped_geom_500m)
                        category_geometries_500m[category].append(geom_rd_500m)
                    if clipped_geom_300m:
                        geom_rd_300m = to_rd_geometry(clipped_geom_300m)
                        category_geometries_300m[category].append(geom_rd_300m)

            except Exception as e:
                log_limited_warning(f"{api_key}_process", f"Failed to process {api_key} feature: {e}")

    _report_progress(on_progress, PROGRESS_CLASSIFIED, "classified BGT features")

    category_merged_geoms_500m = merge_category_geometries(category_geometries_500m)
    category_merged_geoms_300m = merge_category_geometries(category_geometries_300m)

    _report_progress(on_progress, PROGRESS_MERGED, "merged category geometries")

    masked_geoms_500m = mask_category_geometries(category_merged_geoms_500m, OVERLAP_PRIORITY)
    masked_geoms_300m = mask_category_geometries(category_merged_geoms_300m, OVERLAP_PRIORITY)

    percentages_500m = category_percentages(masked_geoms_500m, buffer_area_500m)
    percentages_300m = category_percentages(masked_geoms_300m, buffer_area_300m)

    bebouwd_area_percentage_500m = percentages_500m.get("pand", 0) + percentages_500m.get("bebouwd gebied", 0)
    bebouwd_area_percentage_300m = percentages_300m.get("pand", 0) + percentages_300m.get("bebouwd gebied", 0)

    bkn_unpaved_percentage_300m = unpaved_surface_percentage(masked_geoms_300m, buffer_area_300m)
    bkn_unpaved_percentage_500m = unpaved_surface_percentage(masked_geoms_500m, buffer_area_500m)

    _report_progress(on_progress, PROGRESS_SUMMARISED, "summarising land-cover percentages")

    completed_at = datetime.now(UTC)

    return {
        "process": {
            "name": "nationwide-bgt-land-cover-summary",
            "algorithm_version": ALGORITHM_VERSION,
        },
        "source": {
            "name": SOURCE_NAME,
            "retrieved_at": started_at.isoformat(),
            "collections": BGT_COLLECTION_URLS,
            "feature_counts": {key: len(value) for key, value in features_dict.items()},
            "page_counts": source_page_counts,
        },
        "input": {
            "latitude": lat,
            "longitude": lon,
            "inner_radius_m": buffer_300m,
            "outer_radius_m": buffer_500m,
        },
        "is_partial": bool(fetch_failures),
        "fetch_failures": fetch_failures,
        "classification": {
            "is_official_standard": False,
            "method": (
                "BKN-oriented proxy derived from BGT physical-appearance types; "
                "it does not measure vegetation height or tree-canopy volume."
            ),
            "unpaved_surface_definition": (
                "Union of low, medium, high and unknown vegetation, water, and "
                "BGT terrain explicitly classified as unpaved."
            ),
            "unknown_vegetation_types": sorted(unknown_vegetation_types),
            "overlap_priority": [
                "building",
                "road",
                "built_area",
                "high_vegetation",
                "medium_vegetation",
            ],
        },
        "timing_seconds": {
            "by_collection": source_timings_seconds,
            "total": round(perf_counter() - total_started, 3),
        },
        "completed_at": completed_at.isoformat(),
        "within_inner_radius": summarize_percentages(
            percentages_300m,
            bebouwd_area_percentage_300m,
            bkn_unpaved_percentage_300m,
        ),
        "within_outer_radius": summarize_percentages(
            percentages_500m,
            bebouwd_area_percentage_500m,
            bkn_unpaved_percentage_500m,
        ),
    }
