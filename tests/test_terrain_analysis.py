"""Unit tests for input validation and source handling."""

import pytest

from bkn_terrain_processes.terrain_analysis import get_terrain_analysis_nl


class EmptyFeatureResponse:
    """Minimal successful PDOK response containing no features."""

    def raise_for_status(self):
        return None

    def json(self):
        return {"type": "FeatureCollection", "features": []}


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
        "bkn_terrain_processes.terrain_analysis.requests.get",
        lambda *args, **kwargs: EmptyFeatureResponse(),
    )

    with pytest.raises(
        LookupError,
        match="No PDOK BGT terrain features were found",
    ):
        get_terrain_analysis_nl(0, 0, inner_radius_m=20, outer_radius_m=30)
