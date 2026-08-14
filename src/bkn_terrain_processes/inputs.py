"""Validated execution inputs for the BGT land-cover summary process.

This module defines what a valid analysis request is, independently of
pygeoapi. Asynchronous execution has to reject invalid input at submission
time and calculate later in a worker, so the same definition must be callable
from the API boundary and from a worker that does not serve HTTP.
"""

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_INNER_RADIUS_M = 300
DEFAULT_OUTER_RADIUS_M = 500
MIN_RADIUS_M = 1
MAX_RADIUS_M = 5000


class InvalidInputError(ValueError):
    """Raised when a raw execution request is not a valid analysis request."""


@dataclass(frozen=True)
class AnalysisRequest:
    """One validated analysis request."""

    latitude: float
    longitude: float
    inner_radius_m: int
    outer_radius_m: int


def parse_analysis_request(data: Mapping) -> AnalysisRequest:
    """
    Validate one raw execution request.

    Latitude and longitude range checks still happen inside the calculation
    core; this function currently performs only the checks that the processor
    performed before the extraction.

    :param data: raw execution request inputs
    :raises InvalidInputError: if the request is not a valid analysis request
    :returns: the validated `AnalysisRequest`
    """

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        inner_radius_m = int(data.get("inner_radius_m", DEFAULT_INNER_RADIUS_M))
        outer_radius_m = int(data.get("outer_radius_m", DEFAULT_OUTER_RADIUS_M))
    except (KeyError, TypeError, ValueError) as err:
        raise InvalidInputError("latitude and longitude are required numbers; radii must be integers") from err

    if not MIN_RADIUS_M <= inner_radius_m <= MAX_RADIUS_M:
        raise InvalidInputError(f"inner_radius_m must be between {MIN_RADIUS_M} and {MAX_RADIUS_M} metres")
    if not MIN_RADIUS_M <= outer_radius_m <= MAX_RADIUS_M:
        raise InvalidInputError(f"outer_radius_m must be between {MIN_RADIUS_M} and {MAX_RADIUS_M} metres")
    if inner_radius_m > outer_radius_m:
        raise InvalidInputError("inner_radius_m cannot be larger than outer_radius_m")

    return AnalysisRequest(
        latitude=latitude,
        longitude=longitude,
        inner_radius_m=inner_radius_m,
        outer_radius_m=outer_radius_m,
    )
