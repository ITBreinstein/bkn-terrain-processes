"""Unit tests for execution input validation."""

import pytest

from bkn_terrain_processes.inputs import (
    DEFAULT_INNER_RADIUS_M,
    DEFAULT_OUTER_RADIUS_M,
    MAX_RADIUS_M,
    AnalysisRequest,
    InvalidInputError,
    parse_analysis_request,
)


def test_parse_applies_published_radius_defaults():
    request = parse_analysis_request({"latitude": 52.6324, "longitude": 4.7534})

    assert request == AnalysisRequest(
        latitude=52.6324,
        longitude=4.7534,
        inner_radius_m=DEFAULT_INNER_RADIUS_M,
        outer_radius_m=DEFAULT_OUTER_RADIUS_M,
    )


def test_parse_coerces_numeric_strings():
    request = parse_analysis_request(
        {
            "latitude": "52.6324",
            "longitude": "4.7534",
            "inner_radius_m": "20",
            "outer_radius_m": "30",
        }
    )

    assert request.latitude == 52.6324
    assert request.inner_radius_m == 20


@pytest.mark.parametrize(
    ("data", "expected_message"),
    [
        ({"longitude": 4.7534}, "latitude and longitude are required numbers"),
        ({"latitude": 52.6324}, "latitude and longitude are required numbers"),
        (
            {"latitude": "north", "longitude": 4.7534},
            "latitude and longitude are required numbers",
        ),
        (
            {"latitude": 52.6324, "longitude": 4.7534, "inner_radius_m": 0},
            "inner_radius_m must be between",
        ),
        (
            {
                "latitude": 52.6324,
                "longitude": 4.7534,
                "outer_radius_m": MAX_RADIUS_M + 1,
            },
            "outer_radius_m must be between",
        ),
        (
            {
                "latitude": 52.6324,
                "longitude": 4.7534,
                "inner_radius_m": 600,
                "outer_radius_m": 500,
            },
            "inner_radius_m cannot be larger",
        ),
    ],
)
def test_parse_rejects_invalid_requests(data, expected_message):
    with pytest.raises(InvalidInputError, match=expected_message):
        parse_analysis_request(data)


def test_invalid_input_error_is_a_value_error():
    # Callers outside pygeoapi handle it without importing this module.
    assert issubclass(InvalidInputError, ValueError)
