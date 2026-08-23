"""PDOK BGT collection locations and cursor-pagination handling."""

import logging
from datetime import datetime

import requests
from requests import RequestException

logger = logging.getLogger(__name__)

BGT_COLLECTION_URLS = {
    "begroeid": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/begroeidterreindeel/items",
    "onbegroeid": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/onbegroeidterreindeel/items",
    "water": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/waterdeel/items",
    "weg": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/wegdeel/items",
    "pand": "https://api.pdok.nl/lv/bgt/ogc/v1/collections/pand/items",
}


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
