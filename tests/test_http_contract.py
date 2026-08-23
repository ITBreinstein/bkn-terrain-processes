"""HTTP contract tests for the public BGT process.

The real Flask route, pygeoapi request handling, process manager and processor
are exercised. Only the live PDOK calculation is replaced with a predictable
result so these tests remain deterministic.
"""

from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from summary_result import SUMMARY_RESULT

from bkn_terrain_processes import process
from bkn_terrain_processes.process import SUMMARY_SCHEMA

EXECUTION_PATH = "/processes/bgt-land-cover-summary/execution"
VALID_INPUTS = {
    "latitude": 52.6324,
    "longitude": 4.7534,
    "inner_radius_m": 20,
    "outer_radius_m": 30,
}


@pytest.fixture(scope="module")
def http_client(tmp_path_factory):
    repository = Path(__file__).resolve().parents[1]
    with (repository / "config/pygeoapi.yml").open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    config["server"]["url"] = "http://example.test"
    config["server"]["cors"] = False
    config["server"]["ogc_schemas_location"] = "https://schemas.opengis.net"

    temporary_directory = tmp_path_factory.mktemp("pygeoapi-http-contract")
    config_path = temporary_directory / "pygeoapi.yml"
    openapi_path = temporary_directory / "openapi.yml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    openapi_path.write_text("{}\n", encoding="utf-8")

    environment = pytest.MonkeyPatch()
    environment.setenv("PYGEOAPI_CONFIG", str(config_path))
    environment.setenv("PYGEOAPI_OPENAPI", str(openapi_path))

    from bkn_terrain_processes.app import APP

    APP.config["TESTING"] = True
    yield APP.test_client()
    environment.undo()


@pytest.mark.parametrize("response_mode", [None, "raw"])
def test_synchronous_raw_execution_returns_the_summary_value(http_client, monkeypatch, response_mode):
    expected = SUMMARY_RESULT
    calls = []

    def calculate(latitude, longitude, **kwargs):
        calls.append((latitude, longitude, kwargs))
        return expected

    monkeypatch.setattr(process, "get_terrain_analysis_nl", calculate)
    request = {"inputs": VALID_INPUTS}
    if response_mode is not None:
        request["response"] = response_mode

    response = http_client.post(EXECUTION_PATH, json=request)

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.get_json() == expected
    Draft202012Validator(SUMMARY_SCHEMA).validate(response.get_json())
    assert calls == [
        (
            52.6324,
            4.7534,
            {"inner_radius_m": 20, "outer_radius_m": 30},
        )
    ]


def test_synchronous_document_execution_returns_a_results_map(http_client, monkeypatch):
    expected = SUMMARY_RESULT
    monkeypatch.setattr(process, "get_terrain_analysis_nl", lambda *args, **kwargs: expected)

    response = http_client.post(
        EXECUTION_PATH,
        json={"inputs": VALID_INPUTS, "response": "document"},
    )

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.get_json() == {"summary": {"value": expected}}
    Draft202012Validator(SUMMARY_SCHEMA).validate(response.get_json()["summary"]["value"])


def test_explicit_value_output_selection_returns_the_summary(http_client, monkeypatch):
    expected = SUMMARY_RESULT
    monkeypatch.setattr(process, "get_terrain_analysis_nl", lambda *args, **kwargs: expected)

    response = http_client.post(
        EXECUTION_PATH,
        json={
            "inputs": VALID_INPUTS,
            "outputs": {"summary": {"transmissionMode": "value"}},
        },
    )

    assert response.status_code == 200
    assert response.get_json() == expected


@pytest.mark.parametrize(
    ("changed_input", "invalid_value", "expected_field"),
    [
        ("latitude", "52.6324", "latitude"),
        ("longitude", True, "longitude"),
        ("inner_radius_m", "20", "inner_radius_m"),
        ("outer_radius_m", 30.5, "outer_radius_m"),
    ],
)
def test_execution_rejects_values_that_do_not_match_the_published_schema(
    http_client,
    monkeypatch,
    changed_input,
    invalid_value,
    expected_field,
):
    monkeypatch.setattr(
        process,
        "get_terrain_analysis_nl",
        lambda *args, **kwargs: pytest.fail("calculation must not start for invalid input"),
    )
    inputs = {**VALID_INPUTS, changed_input: invalid_value}

    response = http_client.post(EXECUTION_PATH, json={"inputs": inputs})

    assert response.status_code == 400
    exception = response.get_json()
    assert exception["type"]
    assert exception["code"] == "InvalidParameterValue"
    assert expected_field in exception["description"]


def test_execution_rejects_an_unknown_output(http_client, monkeypatch):
    monkeypatch.setattr(
        process,
        "get_terrain_analysis_nl",
        lambda *args, **kwargs: pytest.fail("calculation must not start for an unknown output"),
    )

    response = http_client.post(
        EXECUTION_PATH,
        json={"inputs": VALID_INPUTS, "outputs": {"unknown": {}}},
    )

    assert response.status_code == 400
    assert "unsupported output: unknown" in response.get_json()["description"]


@pytest.mark.parametrize(
    ("execution_option", "expected_message"),
    [
        ({"outputs": {}}, "outputs must request at least one output"),
        ({"response": "unsupported"}, "response must be either raw or document"),
        (
            {"subscriber": {"successUri": "https://example.test/callback"}},
            "subscriber callbacks are not supported",
        ),
        (
            {"outputs": {"summary": {"transmissionMode": "reference"}}},
            "summary supports only value transmission",
        ),
        (
            {"outputs": {"summary": {"format": {"mediaType": "text/csv"}}}},
            "summary supports only application/json",
        ),
        (
            {"outputs": {"summary": {"format": {"encoding": "base64"}}}},
            "unsupported summary output format member: encoding",
        ),
        (
            {"outputs": {"summary": {"format": {"schema": "https://example.test/schema"}}}},
            "unsupported summary output format member: schema",
        ),
    ],
)
def test_execution_rejects_unadvertised_options(http_client, monkeypatch, execution_option, expected_message):
    monkeypatch.setattr(
        process,
        "get_terrain_analysis_nl",
        lambda *args, **kwargs: pytest.fail("calculation must not start for an unsupported option"),
    )

    response = http_client.post(
        EXECUTION_PATH,
        json={"inputs": VALID_INPUTS, **execution_option},
    )

    assert response.status_code == 400
    assert expected_message in response.get_json()["description"]


@pytest.mark.parametrize(
    ("document", "expected_message"),
    [
        ([], "execution request must be an object"),
        ({"inputs": VALID_INPUTS, "response": []}, "response must be either raw or document"),
        ({"inputs": VALID_INPUTS, "subscriber": "callback"}, "subscriber callbacks are not supported"),
        ({"inputs": VALID_INPUTS, "subscriber": {}}, "subscriber callbacks are not supported"),
        ({"inputs": VALID_INPUTS, "unexpected": True}, "unsupported execution member: unexpected"),
    ],
)
def test_malformed_execution_documents_return_json_400(http_client, monkeypatch, document, expected_message):
    monkeypatch.setattr(
        process,
        "get_terrain_analysis_nl",
        lambda *args, **kwargs: pytest.fail("calculation must not start for a malformed document"),
    )

    response = http_client.post(EXECUTION_PATH, json=document)

    assert response.status_code == 400
    assert response.content_type == "application/json"
    exception = response.get_json()
    assert exception["type"]
    assert exception["code"] == "InvalidParameterValue"
    assert expected_message in exception["description"]


def test_public_description_advertises_only_current_execution_options(http_client):
    response = http_client.get("/processes/bgt-land-cover-summary?f=json")

    assert response.status_code == 200
    description = response.get_json()
    assert description["jobControlOptions"] == ["sync-execute"]
    assert description["outputTransmission"] == ["value"]


def test_public_service_does_not_declare_unverified_callback_conformance(http_client):
    response = http_client.get("/conformance?f=json")

    assert response.status_code == 200
    conformance_classes = response.get_json()["conformsTo"]
    assert "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core" in conformance_classes
    assert "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/callback" not in conformance_classes


def test_unavailable_async_preference_is_ignored_without_a_false_applied_header(http_client, monkeypatch):
    expected = SUMMARY_RESULT
    monkeypatch.setattr(process, "get_terrain_analysis_nl", lambda *args, **kwargs: expected)

    response = http_client.post(
        EXECUTION_PATH,
        json={"inputs": VALID_INPUTS},
        headers={"Prefer": "respond-async"},
    )

    assert response.status_code == 200
    assert response.get_json() == expected
    assert "Preference-Applied" not in response.headers
    assert "Location" not in response.headers


def test_wait_preference_keeps_the_truthful_applied_header(http_client, monkeypatch):
    monkeypatch.setattr(process, "get_terrain_analysis_nl", lambda *args, **kwargs: SUMMARY_RESULT)

    response = http_client.post(
        EXECUTION_PATH,
        json={"inputs": VALID_INPUTS},
        headers={"Prefer": "wait"},
    )

    assert response.status_code == 200
    assert response.headers["Preference-Applied"] == "wait"
