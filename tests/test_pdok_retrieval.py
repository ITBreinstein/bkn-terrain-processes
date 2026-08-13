"""Unit tests for PDOK cursor pagination."""

from datetime import UTC, datetime

import pytest
from requests import Timeout

from bkn_terrain_processes.terrain_analysis import fetch_features_paginated

RETRIEVAL_TIME = datetime(2026, 8, 13, 15, 25, tzinfo=UTC)


class JsonResponse:
    """Minimal successful requests response for controlled page documents."""

    def __init__(self, document):
        self.document = document

    def raise_for_status(self):
        return None

    def json(self):
        return self.document


def test_follows_next_link_and_deduplicates_features(monkeypatch):
    collection_url = "https://api.pdok.example/collections/water/items"
    next_url = f"{collection_url}?cursor=opaque-value&limit=2"
    responses = iter(
        [
            JsonResponse(
                {
                    "features": [{"id": "a"}, {"id": "b"}],
                    "links": [{"rel": "next", "href": next_url}],
                }
            ),
            JsonResponse(
                {
                    "features": [{"id": "b"}, {"id": "c"}],
                    "links": [],
                }
            ),
        ]
    )
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return next(responses)

    monkeypatch.setattr("bkn_terrain_processes.terrain_analysis.requests.get", fake_get)

    features, page_count = fetch_features_paginated(
        collection_url,
        (4.0, 52.0, 4.1, 52.1),
        limit=2,
        retrieval_time=RETRIEVAL_TIME,
    )

    assert [feature["id"] for feature in features] == ["a", "b", "c"]
    assert page_count == 2
    assert calls == [
        (
            collection_url,
            {
                "params": {
                    "bbox": "4.0,52.0,4.1,52.1",
                    "datetime": "2026-08-13T15:25:00Z",
                    "f": "json",
                    "limit": 2,
                },
                "timeout": 30,
            },
        ),
        (next_url, {"params": None, "timeout": 30}),
    ]


def test_rejects_repeated_next_link(monkeypatch):
    collection_url = "https://api.pdok.example/collections/water/items"
    repeated_url = f"{collection_url}?cursor=repeated"
    responses = iter(
        [
            JsonResponse(
                {
                    "features": [{"id": "a"}],
                    "links": [{"rel": "next", "href": repeated_url}],
                }
            ),
            JsonResponse(
                {
                    "features": [{"id": "b"}],
                    "links": [{"rel": "next", "href": repeated_url}],
                }
            ),
        ]
    )
    monkeypatch.setattr(
        "bkn_terrain_processes.terrain_analysis.requests.get",
        lambda *args, **kwargs: next(responses),
    )

    with pytest.raises(ValueError, match="repeated next-page link"):
        fetch_features_paginated(
            collection_url,
            (4.0, 52.0, 4.1, 52.1),
            limit=1,
            retrieval_time=RETRIEVAL_TIME,
        )


def test_retries_only_the_failed_page(monkeypatch):
    collection_url = "https://api.pdok.example/collections/water/items"
    next_url = f"{collection_url}?cursor=second-page"
    responses = iter(
        [
            JsonResponse(
                {
                    "features": [{"id": "a"}],
                    "links": [{"rel": "next", "href": next_url}],
                }
            ),
            Timeout("temporary timeout"),
            JsonResponse({"features": [{"id": "b"}], "links": []}),
        ]
    )
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr("bkn_terrain_processes.terrain_analysis.requests.get", fake_get)

    features, page_count = fetch_features_paginated(
        collection_url,
        (4.0, 52.0, 4.1, 52.1),
        limit=1,
        retrieval_time=RETRIEVAL_TIME,
    )

    assert calls == [collection_url, next_url, next_url]
    assert [feature["id"] for feature in features] == ["a", "b"]
    assert page_count == 2


@pytest.mark.parametrize(
    ("document", "expected_message"),
    [
        ({"features": "not-a-list"}, "'features' must be a list"),
        ({"features": [{}]}, "non-empty string id"),
        (
            {"features": [], "links": [{"rel": "next"}]},
            "next-page link must contain a non-empty href",
        ),
    ],
)
def test_rejects_malformed_page_documents(monkeypatch, document, expected_message):
    monkeypatch.setattr(
        "bkn_terrain_processes.terrain_analysis.requests.get",
        lambda *args, **kwargs: JsonResponse(document),
    )

    with pytest.raises(ValueError, match=expected_message):
        fetch_features_paginated(
            "https://api.pdok.example/collections/water/items",
            (4.0, 52.0, 4.1, 52.1),
            limit=1000,
            retrieval_time=RETRIEVAL_TIME,
        )
