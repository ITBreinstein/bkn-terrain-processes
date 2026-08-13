"""Nationwide BGT land-cover summary for one location in the Netherlands.

The classification below is an application-defined interpretation of BGT
physical appearances, not an official BGT or OGC classification standard.
"""

import logging
from datetime import UTC, datetime
from time import perf_counter

import pyproj
import requests
from requests import RequestException
from shapely.geometry import Point, shape
from shapely.ops import transform, unary_union
from shapely.validation import make_valid

logger = logging.getLogger(__name__)

to_rd = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True).transform
to_wgs = pyproj.Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True).transform

ALGORITHM_VERSION = "0.2.0"
SOURCE_NAME = "PDOK BGT OGC API Features"


def _next_page_url(document: dict) -> str | None:
    """Return the opaque PDOK cursor link without interpreting the cursor."""
    links = document.get("links", [])
    if not isinstance(links, list):
        raise ValueError("PDOK response field 'links' must be a list")

    for link in links:
        if not isinstance(link, dict):
            raise ValueError("PDOK response links must be objects")
        if link.get("rel") == "next":
            href = link.get("href")
            if not isinstance(href, str) or not href:
                raise ValueError("PDOK next-page link must contain a non-empty href")
            return href
    return None


def fetch_features_paginated(
    url: str,
    bounds: tuple[float, float, float, float],
    limit: int,
    retrieval_time: datetime,
    session: requests.Session | None = None,
) -> tuple[list[dict], int]:
    """Retrieve every PDOK page for one collection at one point in time."""
    minx, miny, maxx, maxy = bounds
    request_url = url
    request_params = {
        "bbox": f"{minx},{miny},{maxx},{maxy}",
        "datetime": retrieval_time.isoformat().replace("+00:00", "Z"),
        "f": "json",
        "limit": limit,
    }
    requested_urls = set()
    seen_ids = set()
    features = []
    page_count = 0
    requester = session or requests

    while request_url is not None:
        if request_url in requested_urls:
            raise ValueError("PDOK pagination returned a repeated next-page link")

        for attempt in range(2):
            try:
                response = requester.get(request_url, params=request_params, timeout=30)
                response.raise_for_status()
                break
            except RequestException:
                if attempt == 1:
                    raise
                logger.warning("PDOK page request failed; retrying once: %s", request_url)

        requested_urls.add(request_url)
        document = response.json()
        if not isinstance(document, dict):
            raise ValueError("PDOK response must be a JSON object")

        page_features = document.get("features")
        if not isinstance(page_features, list):
            raise ValueError("PDOK response field 'features' must be a list")
        page_count += 1

        for feature in page_features:
            if not isinstance(feature, dict):
                raise ValueError("PDOK features must be objects")
            feature_id = feature.get("id")
            if not isinstance(feature_id, str) or not feature_id:
                raise ValueError("PDOK feature must contain a non-empty string id")
            if feature_id not in seen_ids:
                seen_ids.add(feature_id)
                features.append(feature)

        request_url = _next_page_url(document)
        request_params = None

    return features, page_count


def get_terrain_analysis_nl(
    lat: float,
    lon: float,
    inner_radius_m: int = 300,
    outer_radius_m: int = 500,
    limit: int = 1000,
):
    """
    Fetch and analyze terrain data around a given lat/lon point.

    Args:
        lat: Latitude of the center point
        lon: Longitude of the center point
        inner_radius_m: Inner analysis radius in metres
        outer_radius_m: Outer analysis radius in metres
        limit: Maximum number of features to fetch per API request

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

    config = {
        "BUFFER_300M": buffer_300m,
        "BUFFER_500M": buffer_500m,
        "LIMIT": limit,
        "lat": lat,
        "lon": lon,
        "CATEGORY_MAP": {
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
        },
        "CATEGORY_TO_COLUMN": {
            "lage vegetatie": "oppervlak_lage_vegetatie_pct",
            "middelhoge vegetatie": "oppervlak_middelhoge_vegetatie_pct",
            "hoge vegetatie": "oppervlak_hoge_vegetatie_pct",
            "onbekende vegetatie": "onbekende_vegetatie_pct",
            "bebouwd gebied": "oppervlak_bebouwd_pct",
            "water": "oppervlak_water_pct",
            "weg": "oppervlak_wegen_pct",
            "pand": "oppervlak_panden_pct",
            "onverhard": "oppervlak_onverhard_pct",
        },
        "API_URLS": {
            "begroeid": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/begroeidterreindeel/items",
            "onbegroeid": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/onbegroeidterreindeel/items",
            "water": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/waterdeel/items",
            "weg": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/wegdeel/items",
            "pand": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/pand/items",
        },
    }

    def get_category(type_value, category_map):
        for category, types in category_map.items():
            if type_value in types:
                return category
        return None

    def clip_feature_to_buffer(geom, buffer_rd):
        try:
            geom_rd = transform(to_rd, geom)
            clipped_geom = geom_rd.intersection(buffer_rd)

            if not clipped_geom.is_valid:
                clipped_geom = make_valid(clipped_geom)

            if clipped_geom.is_empty:
                return None

            return transform(to_wgs, clipped_geom)

        except ValueError as e:
            logger.debug("Geometry value error in clip_feature_to_buffer: %s", e)
            return None

        except TypeError as e:
            logger.debug("Geometry type error in clip_feature_to_buffer: %s", e)
            return None

    station_rd = to_rd(lon, lat)
    buffer_rd_500m = Point(station_rd).buffer(buffer_500m)
    buffer_rd_300m = Point(station_rd).buffer(buffer_300m)
    buffer_wgs_500m = transform(to_wgs, buffer_rd_500m)
    buffer_area_500m = buffer_rd_500m.area
    buffer_area_300m = buffer_rd_300m.area

    bminx, bminy, bmaxx, bmaxy = buffer_wgs_500m.bounds

    features_dict = {}
    source_timings_seconds = {}
    source_page_counts = {}

    fetch_failures = {}

    with requests.Session() as session:
        for key, url in config["API_URLS"].items():
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

    feature_count = sum(len(features) for features in features_dict.values())
    if feature_count == 0:
        if fetch_failures:
            failed_sources = ", ".join(sorted(fetch_failures))
            raise RuntimeError(f"No terrain data could be retrieved; failed PDOK sources: {failed_sources}")
        raise LookupError("No PDOK BGT terrain features were found around this coordinate")

    api_key_to_category = {
        "begroeid": list(config["CATEGORY_MAP"]),
        "onbegroeid": "bebouwd gebied",
        "water": "water",
        "weg": "weg",
        "pand": "pand",
    }

    seen_geometries = set()

    category_geometries_500m = {category: [] for category in config["CATEGORY_TO_COLUMN"]}
    category_geometries_300m = {category: [] for category in config["CATEGORY_TO_COLUMN"]}

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
                clipped_geom_500m = clip_feature_to_buffer(geom, buffer_rd_500m)
                clipped_geom_300m = clip_feature_to_buffer(geom, buffer_rd_300m)

                if clipped_geom_500m or clipped_geom_300m:
                    props = feature["properties"]
                    fysiek_voorkomen = props.get("fysiek_voorkomen", "")
                    plus_fysiek_voorkomen = props.get("plus_fysiek_voorkomen", "")
                    type_value = (
                        f"{fysiek_voorkomen}: {plus_fysiek_voorkomen}" if plus_fysiek_voorkomen else fysiek_voorkomen
                    )

                    category = get_category(type_value, config["CATEGORY_MAP"])
                    if not category:
                        category = "onbekende vegetatie"
                        unknown_vegetation_types.add(type_value or "<empty>")

                    if clipped_geom_500m:
                        geom_rd_500m = transform(to_rd, clipped_geom_500m)
                        category_geometries_500m[category].append(geom_rd_500m)
                    if clipped_geom_300m:
                        geom_rd_300m = transform(to_rd, clipped_geom_300m)
                        category_geometries_300m[category].append(geom_rd_300m)

        except Exception as e:
            log_limited_warning("begroeid_process", f"Failed to process begroeid feature: {e}")

    # Process onbegroeid: split onverhard/zand vs rest (bebouwd gebied)
    onverhard_types = {"onverhard", "zand"}

    for feature in features_dict.get("onbegroeid", []):
        try:
            geom = shape(feature["geometry"])
            geom_wkt = geom.wkt

            if geom_wkt not in seen_geometries:
                seen_geometries.add(geom_wkt)
                clipped_geom_500m = clip_feature_to_buffer(geom, buffer_rd_500m)
                clipped_geom_300m = clip_feature_to_buffer(geom, buffer_rd_300m)

                if clipped_geom_500m or clipped_geom_300m:
                    fv = feature["properties"].get("fysiek_voorkomen", "")
                    category = "onverhard" if fv in onverhard_types else "bebouwd gebied"

                    if clipped_geom_500m:
                        category_geometries_500m[category].append(transform(to_rd, clipped_geom_500m))
                    if clipped_geom_300m:
                        category_geometries_300m[category].append(transform(to_rd, clipped_geom_300m))

        except Exception as e:
            log_limited_warning("onbegroeid_process", f"Failed to process onbegroeid feature: {e}")

    # Process other categories
    for api_key, features in features_dict.items():
        if api_key in ["begroeid", "onbegroeid"]:
            continue

        category = api_key_to_category.get(api_key, api_key)
        if isinstance(category, list) or category not in category_geometries_500m:
            continue

        for feature in features:
            try:
                geom = shape(feature["geometry"])
                geom_wkt = geom.wkt

                if geom_wkt not in seen_geometries:
                    seen_geometries.add(geom_wkt)
                    clipped_geom_500m = clip_feature_to_buffer(geom, buffer_rd_500m)
                    clipped_geom_300m = clip_feature_to_buffer(geom, buffer_rd_300m)

                    if clipped_geom_500m:
                        geom_rd_500m = transform(to_rd, clipped_geom_500m)
                        category_geometries_500m[category].append(geom_rd_500m)
                    if clipped_geom_300m:
                        geom_rd_300m = transform(to_rd, clipped_geom_300m)
                        category_geometries_300m[category].append(geom_rd_300m)

            except Exception as e:
                log_limited_warning(f"{api_key}_process", f"Failed to process {api_key} feature: {e}")

    # Merge geometries
    category_merged_geoms_500m = {}
    category_merged_geoms_300m = {}

    for category, geometries in category_geometries_500m.items():
        if geometries:
            merged_geom = unary_union(geometries)
            category_merged_geoms_500m[category] = None if merged_geom.is_empty else merged_geom
        else:
            category_merged_geoms_500m[category] = None

    for category, geometries in category_geometries_300m.items():
        if geometries:
            merged_geom = unary_union(geometries)
            category_merged_geoms_300m[category] = None if merged_geom.is_empty else merged_geom
        else:
            category_merged_geoms_300m[category] = None

    # Priority masking
    priority_order = ["pand", "weg", "bebouwd gebied", "hoge vegetatie", "middelhoge vegetatie"]
    masked_geoms_500m = {}
    masked_geoms_300m = {}
    covered_area_500m = None
    covered_area_300m = None

    for category in priority_order:
        if category in category_merged_geoms_500m and category_merged_geoms_500m[category]:
            if covered_area_500m is None:
                masked_geoms_500m[category] = category_merged_geoms_500m[category]
            else:
                masked_geoms_500m[category] = category_merged_geoms_500m[category].difference(covered_area_500m)

            if masked_geoms_500m[category].is_empty:
                masked_geoms_500m[category] = None
            else:
                covered_area_500m = (
                    masked_geoms_500m[category]
                    if covered_area_500m is None
                    else covered_area_500m.union(masked_geoms_500m[category])
                )

        if category in category_merged_geoms_300m and category_merged_geoms_300m[category]:
            if covered_area_300m is None:
                masked_geoms_300m[category] = category_merged_geoms_300m[category]
            else:
                masked_geoms_300m[category] = category_merged_geoms_300m[category].difference(covered_area_300m)

            if masked_geoms_300m[category].is_empty:
                masked_geoms_300m[category] = None
            else:
                covered_area_300m = (
                    masked_geoms_300m[category]
                    if covered_area_300m is None
                    else covered_area_300m.union(masked_geoms_300m[category])
                )

    for category in category_merged_geoms_500m:
        if category not in priority_order:
            if category_merged_geoms_500m[category]:
                if covered_area_500m is None:
                    masked_geoms_500m[category] = category_merged_geoms_500m[category]
                else:
                    masked_geoms_500m[category] = category_merged_geoms_500m[category].difference(covered_area_500m)
                    if masked_geoms_500m[category].is_empty:
                        masked_geoms_500m[category] = None
            else:
                masked_geoms_500m[category] = None

            if category_merged_geoms_300m[category]:
                if covered_area_300m is None:
                    masked_geoms_300m[category] = category_merged_geoms_300m[category]
                else:
                    masked_geoms_300m[category] = category_merged_geoms_300m[category].difference(covered_area_300m)
                    if masked_geoms_300m[category].is_empty:
                        masked_geoms_300m[category] = None
            else:
                masked_geoms_300m[category] = None

    category_areas_500m = {}
    category_areas_300m = {}

    for category, geom in masked_geoms_500m.items():
        if geom:
            category_areas_500m[category] = geom.area

    for category, geom in masked_geoms_300m.items():
        if geom:
            category_areas_300m[category] = geom.area

    percentages_500m = {cat: (area / buffer_area_500m) * 100 for cat, area in category_areas_500m.items()}
    percentages_300m = {cat: (area / buffer_area_300m) * 100 for cat, area in category_areas_300m.items()}

    bebouwd_area_percentage_500m = percentages_500m.get("pand", 0) + percentages_500m.get("bebouwd gebied", 0)
    bebouwd_area_percentage_300m = percentages_300m.get("pand", 0) + percentages_300m.get("bebouwd gebied", 0)

    bkn_unpaved_categories = {
        "lage vegetatie",
        "middelhoge vegetatie",
        "hoge vegetatie",
        "onbekende vegetatie",
        "water",
        "onverhard",
    }

    def unpaved_surface_percentage(masked_geometries, buffer_area):
        """Calculate BKN-oriented unpaved surface without double-counting overlaps."""
        geometries = [
            geometry
            for category, geometry in masked_geometries.items()
            if category in bkn_unpaved_categories and geometry is not None
        ]
        if not geometries:
            return 0.0
        return (unary_union(geometries).area / buffer_area) * 100

    bkn_unpaved_percentage_300m = unpaved_surface_percentage(masked_geoms_300m, buffer_area_300m)
    bkn_unpaved_percentage_500m = unpaved_surface_percentage(masked_geoms_500m, buffer_area_500m)

    def summarize(percentages, built_percentage, bkn_unpaved_percentage):
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

    completed_at = datetime.now(UTC)

    return {
        "process": {
            "name": "nationwide-bgt-land-cover-summary",
            "algorithm_version": ALGORITHM_VERSION,
        },
        "source": {
            "name": SOURCE_NAME,
            "retrieved_at": started_at.isoformat(),
            "collections": config["API_URLS"],
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
        "within_inner_radius": summarize(
            percentages_300m,
            bebouwd_area_percentage_300m,
            bkn_unpaved_percentage_300m,
        ),
        "within_outer_radius": summarize(
            percentages_500m,
            bebouwd_area_percentage_500m,
            bkn_unpaved_percentage_500m,
        ),
    }
