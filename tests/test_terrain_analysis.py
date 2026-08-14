"""Unit tests for input validation, source handling and progress reporting."""

import pytest

from bkn_terrain_processes.terrain_analysis import (
    PROGRESS_FETCH_COMPLETE,
    PROGRESS_FETCH_START,
    PROGRESS_SUMMARISED,
    get_terrain_analysis_nl,
)

TEST_LATITUDE = 52.6324
TEST_LONGITUDE = 4.7534

# Covers the whole analysis buffer used by the tests below.
COVERING_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [4.7500, 52.6300],
            [4.7600, 52.6300],
            [4.7600, 52.6350],
            [4.7500, 52.6350],
            [4.7500, 52.6300],
        ]
    ],
}


class EmptyFeatureResponse:
    """Minimal successful PDOK response containing no features."""

    def raise_for_status(self):
        return None

    def json(self):
        return {"type": "FeatureCollection", "features": []}


class SingleFeatureResponse:
    """Minimal successful PDOK response containing one covering feature."""

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "test-feature",
                    "type": "Feature",
                    "geometry": COVERING_POLYGON,
                    "properties": {"fysiek_voorkomen": "loofbos"},
                }
            ],
        }


@pytest.mark.parametrize(
    ("latitude", "longitude", "expected_message"),
    [
        (91, 5, "lat must be between -90 and 90"),
        (52, 181, "lon must be between -180 and 180"),
    ],
)
def test_rejects_invalid_coordinates(latitude, longitude, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        get_terrain_analysis_nl(latitude, longitude)


def test_rejects_inner_radius_larger_than_outer_radius():
    with pytest.raises(
        ValueError,
        match="inner_radius_m cannot be larger than outer_radius_m",
    ):
        get_terrain_analysis_nl(52.6324, 4.7534, inner_radius_m=600, outer_radius_m=500)


def test_reports_no_pdok_coverage_instead_of_zero_percentages(monkeypatch):
    monkeypatch.setattr(
        "bkn_terrain_processes.terrain_analysis.requests.Session.get",
        lambda *args, **kwargs: EmptyFeatureResponse(),
    )

    with pytest.raises(
        LookupError,
        match="No PDOK BGT terrain features were found",
    ):
        get_terrain_analysis_nl(0, 0, inner_radius_m=20, outer_radius_m=30)


@pytest.fixture
def covered_pdok(monkeypatch):
    """Serve one covering feature for every BGT collection."""

    monkeypatch.setattr(
        "bkn_terrain_processes.terrain_analysis.requests.Session.get",
        lambda *args, **kwargs: SingleFeatureResponse(),
    )


def run_analysis(**kwargs):
    return get_terrain_analysis_nl(
        TEST_LATITUDE,
        TEST_LONGITUDE,
        inner_radius_m=20,
        outer_radius_m=30,
        **kwargs,
    )


def test_progress_is_not_reported_without_a_callback(covered_pdok):
    # The synchronous path passes no callback and must be unaffected.
    assert run_analysis()["process"]["algorithm_version"]


def test_progress_advances_monotonically_to_a_terminal_phase(covered_pdok):
    reported = []

    run_analysis(on_progress=lambda percent, message: reported.append((percent, message)))

    percentages = [percent for percent, _ in reported]
    assert percentages == sorted(percentages)
    assert percentages[0] == PROGRESS_FETCH_START
    assert percentages[-1] == PROGRESS_SUMMARISED
    # Every collection reports once, and the last one closes the fetch phase.
    assert PROGRESS_FETCH_COMPLETE in percentages


def test_progress_messages_name_each_retrieved_collection(covered_pdok):
    reported = []

    run_analysis(on_progress=lambda percent, message: reported.append((percent, message)))

    messages = " | ".join(message for _, message in reported)
    for collection in ("begroeid", "onbegroeid", "water", "weg", "pand"):
        assert f"retrieved BGT collection {collection}" in messages


def test_failing_progress_callback_does_not_lose_the_calculation(covered_pdok, caplog):
    def broken_callback(percent, message):
        raise RuntimeError("job store unavailable")

    result = run_analysis(on_progress=broken_callback)

    assert result["process"]["algorithm_version"]
    assert "Progress callback failed" in caplog.text
