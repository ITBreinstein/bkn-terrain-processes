"""Unit tests for the pygeoapi processor boundary."""

from jsonschema import Draft202012Validator
from pygeoapi.process.base import ProcessorExecuteError

from bkn_terrain_processes import process
from bkn_terrain_processes.process import (
    PROCESS_METADATA,
    SUMMARY_SCHEMA,
    BgtLandCoverSummaryProcessor,
)

PROCESSOR_DEFINITION = {"name": "bkn_terrain_processes.process.BgtLandCoverSummaryProcessor"}


def test_published_output_schema_is_valid_json_schema():
    Draft202012Validator.check_schema(SUMMARY_SCHEMA)


def test_process_metadata_advertises_only_implemented_modes():
    assert PROCESS_METADATA["id"] == "bgt-land-cover-summary"
    assert PROCESS_METADATA["jobControlOptions"] == ["sync-execute"]
    assert PROCESS_METADATA["outputTransmission"] == ["value"]
    assert PROCESS_METADATA["outputs"]["summary"]["schema"]["required"]


def test_execute_returns_named_pygeoapi_output(monkeypatch):
    expected = {"process": {"algorithm_version": "test"}}
    monkeypatch.setattr(
        process,
        "get_terrain_analysis_nl",
        lambda *args, **kwargs: expected,
    )
    processor = BgtLandCoverSummaryProcessor(PROCESSOR_DEFINITION)

    media_type, output = processor.execute(
        {
            "latitude": 52.6324,
            "longitude": 4.7534,
            "inner_radius_m": 20,
            "outer_radius_m": 30,
        }
    )

    assert media_type == "application/json"
    assert output == {"id": "summary", "value": expected}


def test_execute_rejects_unknown_output(monkeypatch):
    monkeypatch.setattr(
        process,
        "get_terrain_analysis_nl",
        lambda *args, **kwargs: {"result": "unused"},
    )
    processor = BgtLandCoverSummaryProcessor(PROCESSOR_DEFINITION)

    try:
        processor.execute(
            {"latitude": 52.6324, "longitude": 4.7534},
            outputs={"different-output": {}},
        )
    except ProcessorExecuteError as error:
        assert "unsupported output: different-output" in str(error)
    else:
        raise AssertionError("ProcessorExecuteError was not raised")


def test_execute_rejects_invalid_radius_order():
    processor = BgtLandCoverSummaryProcessor(PROCESSOR_DEFINITION)

    try:
        processor.execute(
            {
                "latitude": 52.6324,
                "longitude": 4.7534,
                "inner_radius_m": 600,
                "outer_radius_m": 500,
            }
        )
    except ProcessorExecuteError as error:
        assert "inner_radius_m cannot be larger" in str(error)
    else:
        raise AssertionError("ProcessorExecuteError was not raised")
