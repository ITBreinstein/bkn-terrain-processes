"""Focused tests for the integration-only CITE echo process."""

import pytest
from jsonschema import Draft202012Validator
from pygeoapi.process.base import ProcessorExecuteError
from test_processes import async_echo

PROCESSOR_DEFINITION = {"name": "test_processes.async_echo.AsyncEchoProcessor"}


def test_metadata_matches_the_cite_echo_contract():
    metadata = async_echo.PROCESS_METADATA

    assert metadata["id"] == "async-echo"
    assert metadata["jobControlOptions"] == ["sync-execute", "async-execute"]
    assert list(metadata["inputs"]) == ["message", "pause"]
    assert metadata["inputs"]["message"]["schema"] == {"type": "string"}
    assert metadata["inputs"]["pause"]["schema"]["type"] == "integer"
    assert metadata["outputs"]["message"]["schema"] == {"type": "string"}

    for definition in (*metadata["inputs"].values(), *metadata["outputs"].values()):
        Draft202012Validator.check_schema(definition["schema"])


def test_execute_returns_the_supplied_message_and_pause(monkeypatch):
    pauses = []
    monkeypatch.setattr(async_echo.time, "sleep", pauses.append)
    processor = async_echo.AsyncEchoProcessor(PROCESSOR_DEFINITION)

    media_type, output = processor.execute({"message": "teststring", "pause": 5})

    assert pauses == [5]
    assert media_type == "application/json"
    assert output == {"id": "message", "value": "teststring"}


def test_execute_defaults_to_no_pause(monkeypatch):
    pauses = []
    monkeypatch.setattr(async_echo.time, "sleep", pauses.append)
    processor = async_echo.AsyncEchoProcessor(PROCESSOR_DEFINITION)

    _, output = processor.execute({"message": "teststring"})

    assert pauses == [0]
    assert output == {"id": "message", "value": "teststring"}


def test_execute_honours_output_selection(monkeypatch):
    monkeypatch.setattr(async_echo.time, "sleep", lambda _seconds: None)
    processor = async_echo.AsyncEchoProcessor(PROCESSOR_DEFINITION)

    _, output = processor.execute(
        {"message": "teststring"},
        outputs={"different-output": {}},
    )

    assert output == {}


@pytest.mark.parametrize(
    ("data", "expected_message"),
    [
        ({}, "message must be a string"),
        ({"message": 1}, "message must be a string"),
        ({"message": "test", "pause": "5"}, "pause must be an integer"),
        ({"message": "test", "pause": True}, "pause must be an integer"),
        ({"message": "test", "pause": -1}, "pause must be between"),
        ({"message": "test", "pause": 61}, "pause must be between"),
    ],
)
def test_execute_rejects_invalid_input(data, expected_message):
    processor = async_echo.AsyncEchoProcessor(PROCESSOR_DEFINITION)

    with pytest.raises(ProcessorExecuteError, match=expected_message):
        processor.execute(data)
