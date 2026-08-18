"""Validated execution inputs for the BGT land-cover summary process.

This module defines what a valid analysis request is, independently of
pygeoapi. Asynchronous execution has to reject invalid input at submission
time and calculate later in a worker, so the same definition must be callable
from the API boundary and from a worker that does not serve HTTP.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite

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

    :param data: raw execution request inputs
    :raises InvalidInputError: if the request is not a valid analysis request
    :returns: the validated `AnalysisRequest`
    """

    if not isinstance(data, Mapping):
        raise InvalidInputError("inputs must be an object")

    allowed_inputs = {
        "latitude",
        "longitude",
        "inner_radius_m",
        "outer_radius_m",
    }
    unknown_inputs = sorted(set(data) - allowed_inputs)
    if unknown_inputs:
        raise InvalidInputError(f"unsupported input: {unknown_inputs[0]}")

    latitude = _required_number(data, "latitude")
    longitude = _required_number(data, "longitude")
    inner_radius_m = _optional_integer(data, "inner_radius_m", DEFAULT_INNER_RADIUS_M)
    outer_radius_m = _optional_integer(data, "outer_radius_m", DEFAULT_OUTER_RADIUS_M)

    if not -90 <= latitude <= 90:
        raise InvalidInputError("latitude must be between -90 and 90 degrees")
    if not -180 <= longitude <= 180:
        raise InvalidInputError("longitude must be between -180 and 180 degrees")

    if not MIN_RADIUS_M <= inner_radius_m <= MAX_RADIUS_M:
        raise InvalidInputError(f"inner_radius_m must be between {MIN_RADIUS_M} and {MAX_RADIUS_M} metres")
    if not MIN_RADIUS_M <= outer_radius_m <= MAX_RADIUS_M:
        raise InvalidInputError(f"outer_radius_m must be between {MIN_RADIUS_M} and {MAX_RADIUS_M} metres")
    if inner_radius_m > outer_radius_m:
        raise InvalidInputError("inner_radius_m cannot be larger than outer_radius_m")

    return AnalysisRequest(
        latitude=float(latitude),
        longitude=float(longitude),
        inner_radius_m=inner_radius_m,
        outer_radius_m=outer_radius_m,
    )


def _required_number(data: Mapping, name: str) -> int | float:
    """Return one finite JSON number without coercing strings or booleans."""

    if name not in data:
        raise InvalidInputError(f"{name} is required")

    value = data[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidInputError(f"{name} must be a finite number")
    if isinstance(value, float) and not isfinite(value):
        raise InvalidInputError(f"{name} must be a finite number")
    return value


def _optional_integer(data: Mapping, name: str, default: int) -> int:
    """Return one JSON-Schema integer, applying its published default."""

    value = data.get(name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidInputError(f"{name} must be an integer")
    if isinstance(value, float) and (not isfinite(value) or not value.is_integer()):
        raise InvalidInputError(f"{name} must be an integer")
    return int(value)
