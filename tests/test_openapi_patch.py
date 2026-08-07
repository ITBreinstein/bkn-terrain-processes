"""Regression tests for the generated Processes OpenAPI corrections."""

from scripts.patch_pygeoapi_openapi import (
    SCHEMA_BASE,
    patch_openapi_document,
)


def _generated_document():
    return {
        "paths": {
            "/conformance": {"get": {"responses": {"200": {"$ref": "wrong-landing-page"}}}},
            "/processes": {
                "get": {
                    "parameters": [{"$ref": "#/components/parameters/f"}],
                    "responses": {"200": {"$ref": "processes-1.0-list"}},
                }
            },
            "/processes/bgt-land-cover-summary": {"get": {"responses": {"200": {"description": "ok"}}}},
            "/processes/bgt-land-cover-summary/execution": {"post": {"responses": {"200": {"description": "ok"}}}},
        }
    }


def test_patch_describes_conformance_process_list_limit_and_404():
    document = patch_openapi_document(_generated_document(), 10, 50)

    conformance_schema = document["paths"]["/conformance"]["get"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    assert conformance_schema == {"$ref": f"{SCHEMA_BASE}/confClasses.yaml"}

    process_operation = document["paths"]["/processes"]["get"]
    limit = next(parameter for parameter in process_operation["parameters"] if parameter.get("name") == "limit")
    assert limit["in"] == "query"
    assert limit["schema"] == {
        "type": "integer",
        "minimum": 1,
        "maximum": 50,
        "default": 10,
    }
    assert process_operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": f"{SCHEMA_BASE}/processList.yaml"
    }

    process_responses = document["paths"]["/processes/bgt-land-cover-summary"]["get"]["responses"]
    assert process_responses["404"]["content"]["application/json"]["schema"] == {
        "$ref": f"{SCHEMA_BASE}/exception.yaml"
    }


def test_patch_does_not_add_404_to_execution_operation():
    document = patch_openapi_document(_generated_document(), 10, 50)

    execution = document["paths"]["/processes/bgt-land-cover-summary/execution"]
    assert "get" not in execution
