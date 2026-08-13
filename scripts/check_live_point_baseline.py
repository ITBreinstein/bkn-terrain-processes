"""Compare current live-PDOK point results with recorded expectations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bkn_terrain_processes.terrain_analysis import get_terrain_analysis_nl

DATA_DIRECTORY = Path(__file__).parents[1] / "tests" / "data" / "point_baseline"
EXIT_BASELINE_MISMATCH = 1
EXIT_SOURCE_UNAVAILABLE = 2
EXIT_APPLICATION_ERROR = 3


def classify_execution_error(error: Exception) -> str:
    """Distinguish missing live data from an unexpected application error."""
    if isinstance(error, RuntimeError) and str(error).startswith(
        "No terrain data could be retrieved; failed PDOK sources:"
    ):
        return "source_unavailable"
    if isinstance(error, LookupError):
        return "result_unavailable"
    return "application_error"


def load_data() -> tuple[dict[str, Any], dict[str, Any]]:
    with (DATA_DIRECTORY / "cases.json").open(encoding="utf-8") as source:
        catalogue = json.load(source)
    with (DATA_DIRECTORY / "expected-results.json").open(encoding="utf-8") as source:
        expectations = json.load(source)
    return catalogue, expectations["results"]


def compare_expected(
    expected: Any,
    actual: Any,
    tolerance: float,
    path: str = "result",
) -> list[str]:
    """Compare only fields present in an expected, possibly partial document."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected an object, got {type(actual).__name__}"]
        differences = []
        for key, expected_value in expected.items():
            if key not in actual:
                differences.append(f"{path}.{key}: missing")
                continue
            differences.extend(compare_expected(expected_value, actual[key], tolerance, f"{path}.{key}"))
        return differences

    if isinstance(expected, int | float) and not isinstance(expected, bool):
        if not isinstance(actual, int | float) or isinstance(actual, bool):
            return [f"{path}: expected {expected}, got {actual!r}"]
        if abs(float(expected) - float(actual)) > tolerance:
            return [f"{path}: expected {expected}, got {actual}"]
        return []

    if expected != actual:
        return [f"{path}: expected {expected!r}, got {actual!r}"]
    return []


def stable_result(result: dict[str, Any]) -> dict[str, Any]:
    """Exclude timestamps, timings and source counts from comparison."""
    return {
        "is_partial": result["is_partial"],
        "fetch_failures": result["fetch_failures"],
        "within_inner_radius": result["within_inner_radius"],
        "within_outer_radius": result["within_outer_radius"],
    }


def main() -> int:
    catalogue, expectations = load_data()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="case_ids", help="Check only this case ID (repeatable)")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=catalogue["default_tolerance_percentage_points"],
        help="Allowed numeric difference in percentage points",
    )
    args = parser.parse_args()

    selected = [case for case in catalogue["cases"] if not args.case_ids or case["id"] in args.case_ids]
    unknown_ids = set(args.case_ids or []) - {case["id"] for case in selected}
    if unknown_ids:
        parser.error(f"Unknown case IDs: {', '.join(sorted(unknown_ids))}")

    domain_failures = []
    historical_differences = []
    for case in selected:
        case_id = case["id"]
        print(f"CHECK {case_id}: {case['label']}", flush=True)
        try:
            current = get_terrain_analysis_nl(
                case["latitude"],
                case["longitude"],
                inner_radius_m=catalogue["default_inner_radius_m"],
                outer_radius_m=catalogue["default_outer_radius_m"],
            )
        except Exception as error:  # Classify before deciding whether CI should retry.
            error_kind = classify_execution_error(error)
            if error_kind == "source_unavailable":
                print(f"EXTERNAL SERVICE UNAVAILABLE {case_id}: {error}")
                print("SUMMARY Live PDOK data could not be retrieved")
                return EXIT_SOURCE_UNAVAILABLE
            if error_kind == "application_error":
                print(f"APPLICATION ERROR {case_id}: {type(error).__name__}: {error}")
                print("SUMMARY The calculation raised an unexpected error")
                return EXIT_APPLICATION_ERROR

            differences = [f"result: expected a calculation result, got no PDOK features: {error}"]
        else:
            if current["is_partial"]:
                failed_sources = ", ".join(sorted(current["fetch_failures"]))
                print(f"EXTERNAL SERVICE UNAVAILABLE {case_id}: incomplete PDOK data from {failed_sources}")
                print("SUMMARY Live PDOK data was incomplete")
                return EXIT_SOURCE_UNAVAILABLE

            differences = compare_expected(
                expectations[case_id],
                stable_result(current),
                args.tolerance,
            )

        if not differences:
            print(f"PASS {case_id}")
            continue

        if case["evidence"] == "domain_assertion":
            domain_failures.append(case_id)
            severity = "FAIL"
        else:
            historical_differences.append(case_id)
            severity = "WARNING"
        print(f"{severity} {case_id}: result differs from {case['evidence']}")
        for difference in differences:
            print(f"  - {difference}")

    historical_problem_count = len(historical_differences)
    widespread_change = historical_problem_count >= catalogue["historical_failure_threshold"]

    print(f"SUMMARY domain failures={len(domain_failures)}, historical differences={len(historical_differences)}")
    if domain_failures or widespread_change:
        print("FAIL Live point baseline requires investigation")
        return EXIT_BASELINE_MISMATCH
    if historical_differences:
        print("WARNING Isolated differences require review but may reflect local PDOK changes")
    else:
        print("PASS All live point results match their recorded expectations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
