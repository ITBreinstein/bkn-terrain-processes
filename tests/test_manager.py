"""Unit tests for the OGC result formatter around pygeoapi."""

import pytest

from bkn_terrain_processes.manager import format_process_result


def test_format_raw_response_returns_single_output_value():
    result = {"sentinel": "terrain-result"}

    assert format_process_result({"id": "summary", "value": result}, "raw") == result


def test_format_document_response_uses_output_identifier_as_key():
    result = {"sentinel": "terrain-result"}

    assert format_process_result({"id": "summary", "value": result}, "document") == {"summary": {"value": result}}


def test_format_document_response_keeps_scalar_output_inline():
    assert format_process_result({"id": "message", "value": "hello"}, "document") == {"message": "hello"}


@pytest.mark.parametrize(
    "invalid_output",
    [
        None,
        {},
        {"value": {}},
        {"id": "summary"},
        {"id": "", "value": {}},
        {"id": "summary", "value": {}, "extra": True},
    ],
)
def test_format_rejects_invalid_internal_output(invalid_output):
    with pytest.raises(ValueError):
        format_process_result(invalid_output, "raw")
