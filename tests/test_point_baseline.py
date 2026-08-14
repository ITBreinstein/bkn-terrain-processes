"""Deterministic validation of the live point-baseline data and comparator."""

import sys

import pytest

import scripts.check_live_point_baseline as point_baseline
from scripts.check_live_point_baseline import classify_execution_error, compare_expected, load_data


def test_point_baseline_catalogue_is_complete_and_explicit():
    catalogue, expectations = load_data()
    cases = catalogue["cases"]

    assert len(cases) == 8
    assert len({case["id"] for case in cases}) == 8
    assert {case["id"] for case in cases} == set(expectations)
    assert [case["evidence"] for case in cases].count("domain_assertion") == 2
    assert [case["evidence"] for case in cases].count("historical_baseline") == 6

    for case in cases:
        assert 50 <= case["latitude"] <= 54
        assert 3 <= case["longitude"] <= 8


def test_water_assertions_are_manual_partial_expectations():
    catalogue, expectations = load_data()
    water_cases = [case for case in catalogue["cases"] if case["evidence"] == "domain_assertion"]

    for case in water_cases:
        expected = expectations[case["id"]]
        for area_name in ("within_inner_radius", "within_outer_radius"):
            indicators = expected[area_name]["bkn_indicators"]
            assert indicators["water_surface_pct"] == 100.0
            assert "unpaved_surface_proxy_pct" not in indicators


def test_comparator_supports_partial_documents_and_numeric_tolerance():
    expected = {"area": {"water_surface_pct": 100.0}}

    assert compare_expected(expected, {"area": {"water_surface_pct": 99.97, "ignored": 12}}, 0.05) == []
    assert compare_expected(expected, {"area": {"water_surface_pct": 99.8}}, 0.05) == [
        "result.area.water_surface_pct: expected 100.0, got 99.8"
    ]


def test_execution_errors_identify_external_data_failures():
    external_error = RuntimeError("No terrain data could be retrieved; failed PDOK sources: begroeid, water")

    assert classify_execution_error(external_error) == "source_unavailable"
    assert classify_execution_error(LookupError("No PDOK features found")) == "result_unavailable"
    assert classify_execution_error(TypeError("calculation bug")) == "application_error"


@pytest.mark.parametrize(
    ("error", "expected_exit_code"),
    [
        (
            RuntimeError("No terrain data could be retrieved; failed PDOK sources: water"),
            point_baseline.EXIT_SOURCE_UNAVAILABLE,
        ),
        (TypeError("calculation bug"), point_baseline.EXIT_APPLICATION_ERROR),
    ],
)
def test_checker_returns_distinct_exit_codes(monkeypatch, error, expected_exit_code):
    catalogue = {
        "default_inner_radius_m": 300,
        "default_outer_radius_m": 500,
        "default_tolerance_percentage_points": 0.05,
        "historical_failure_threshold": 4,
        "cases": [
            {
                "id": "example",
                "label": "Example",
                "latitude": 52.0,
                "longitude": 5.0,
                "evidence": "historical_baseline",
            }
        ],
    }

    def raise_error(*args, **kwargs):
        raise error

    monkeypatch.setattr(point_baseline, "load_data", lambda: (catalogue, {"example": {}}))
    monkeypatch.setattr(point_baseline, "get_terrain_analysis_nl", raise_error)
    monkeypatch.setattr(sys, "argv", ["check_live_point_baseline.py"])

    assert point_baseline.main() == expected_exit_code


@pytest.mark.parametrize(
    ("strict_argument", "expected_exit_code"),
    [
        ([], 0),
        (["--strict-historical"], point_baseline.EXIT_BASELINE_MISMATCH),
    ],
)
def test_strict_mode_turns_an_isolated_historical_difference_into_a_failure(
    monkeypatch,
    strict_argument,
    expected_exit_code,
):
    catalogue = {
        "default_inner_radius_m": 300,
        "default_outer_radius_m": 500,
        "default_tolerance_percentage_points": 0.05,
        "historical_failure_threshold": 4,
        "cases": [
            {
                "id": "example",
                "label": "Example",
                "latitude": 52.0,
                "longitude": 5.0,
                "evidence": "historical_baseline",
            }
        ],
    }
    current = {
        "is_partial": False,
        "fetch_failures": {},
        "within_inner_radius": {"water_surface_pct": 20.0},
        "within_outer_radius": {},
        "timing_seconds": {"total": 0.01, "by_collection": {}},
        "source": {"page_counts": {}, "feature_counts": {}},
    }

    monkeypatch.setattr(
        point_baseline,
        "load_data",
        lambda: (catalogue, {"example": {"within_inner_radius": {"water_surface_pct": 10.0}}}),
    )
    monkeypatch.setattr(point_baseline, "get_terrain_analysis_nl", lambda *args, **kwargs: current)
    monkeypatch.setattr(sys, "argv", ["check_live_point_baseline.py", *strict_argument])

    assert point_baseline.main() == expected_exit_code
