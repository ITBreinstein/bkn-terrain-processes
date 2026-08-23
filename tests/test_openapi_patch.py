"""Regression tests for the generated Processes OpenAPI corrections."""

from scripts.patch_pygeoapi_openapi import (
    SCHEMA_BASE,
    patch_openapi_document,
)


def _generated_document():
    return {
        "info": {
            "title": "BGT Land-cover Summary API",
            "version": "0.23.4",
            "contact": {"name": None},
        },
        "tags": [
            {"name": "server"},
            {"name": "coverages"},
            {"name": "features"},
            {"name": "jobs"},
            {"name": "processes"},
        ],
        "paths": {
            "/": {
                "get": {
                    "tags": ["server"],
                    "responses": {
                        "200": {
                            "description": "generic",
                            "content": {"application/json": {"example": {"title": "Buildings in Bonn"}}},
                        }
                    },
                }
            },
            "/collections": {"get": {"tags": ["server"], "responses": {"200": {}}}},
            "/conformance": {
                "get": {
                    "tags": ["server"],
                    "responses": {"200": {"$ref": "wrong-landing-page"}},
                }
            },
            "/jobs": {"get": {"tags": ["jobs"], "responses": {"200": {}}}},
            "/jobs/{jobId}": {"get": {"tags": ["jobs"], "responses": {"404": {}}}},
            "/processes": {
                "get": {
                    "tags": ["server"],
                    "parameters": [{"$ref": "#/components/parameters/f"}],
                    "responses": {"200": {"$ref": "processes-1.0-list"}},
                }
            },
            "/processes/bgt-land-cover-summary": {
                "get": {
                    "tags": ["bgt-land-cover-summary"],
                    "responses": {"200": {"description": "ok"}},
                }
            },
            "/processes/bgt-land-cover-summary/execution": {
                "post": {
                    "tags": ["bgt-land-cover-summary"],
                    "parameters": [
                        {
                            "name": "Prefer",
                            "in": "header",
                            "schema": {"type": "string", "enum": ["respond-sync"]},
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"subscriber": {"type": "object"}},
                                }
                            }
                        }
                    },
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
        },
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

    execution = document["paths"]["/processes/bgt-land-cover-summary/execution"]["post"]
    assert execution["parameters"] == []

    request = execution["requestBody"]["content"]["application/json"]
    assert request["example"]["inputs"]["latitude"] == 52.6324
    request_schema = request["schema"]
    assert request_schema["required"] == ["inputs"]
    assert set(request_schema["properties"]) == {"inputs", "outputs", "response"}
    assert request_schema["properties"]["inputs"]["required"] == ["latitude", "longitude"]
    assert request_schema["properties"]["response"]["enum"] == ["raw", "document"]
    assert "subscriber" not in request_schema["properties"]


def test_patch_publishes_only_relevant_product_documentation():
    document = patch_openapi_document(_generated_document(), 10, 50)

    assert document["info"]["version"] == "0.2.0"
    assert "contact" not in document["info"]
    assert "/collections" not in document["paths"]
    assert not any(path == "/jobs" or path.startswith("/jobs/") for path in document["paths"])
    assert document["tags"] == [{"name": "Service information"}]

    service_operations = [
        operation
        for path_item in document["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "Service information" in operation.get("tags", [])
    ]
    assert service_operations
    assert all("server" not in operation.get("tags", []) for operation in service_operations)

    landing_example = document["paths"]["/"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    assert landing_example["title"] == "BGT Land-cover Summary API"
    assert "Bonn" not in str(landing_example)


def test_patch_keeps_generic_job_documentation_for_integration_configuration():
    document = _generated_document()
    document["paths"].pop("/processes/bgt-land-cover-summary/execution")
    document["paths"]["/processes/async-echo"] = document["paths"].pop("/processes/bgt-land-cover-summary")

    patched = patch_openapi_document(document, 10, 50)

    assert "/collections" in patched["paths"]
    assert "/jobs" in patched["paths"]
    assert patched["info"]["version"] == "0.23.4"
    assert {tag["name"] for tag in patched["tags"]} >= {"server", "jobs"}
