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
            "/processes/bgt-land-cover-summary/execution": {
                "post": {
                    "parameters": [
                        {
                            "name": "Prefer",
                            "in": "header",
                            "schema": {"type": "string", "enum": ["respond-sync"]},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["process"],
                                        "properties": {"process": {"type": "object"}},
                                    }
                                }
                            },
                        },
                        "201": {"description": "async"},
                    },
                }
            },
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


def test_patch_describes_synchronous_success_and_validation_responses():
    document = patch_openapi_document(_generated_document(), 10, 50)

    responses = document["paths"]["/processes/bgt-land-cover-summary/execution"]["post"]["responses"]
    assert "201" not in responses
    assert responses["400"]["content"]["application/json"]["schema"] == {"$ref": f"{SCHEMA_BASE}/exception.yaml"}

    success_schema = responses["200"]["content"]["application/json"]["schema"]
    raw_schema, document_schema = success_schema["oneOf"]
    assert raw_schema["required"] == ["process"]
    assert document_schema == {
        "type": "object",
        "required": ["summary"],
        "properties": {
            "summary": {
                "type": "object",
                "required": ["value"],
                "properties": {"value": raw_schema},
                "additionalProperties": False,
            }
        },
        "additionalProperties": False,
    }

    prefer_parameter = document["paths"]["/processes/bgt-land-cover-summary/execution"]["post"]["parameters"][0]
    assert prefer_parameter["schema"]["enum"] == ["respond-async"]
