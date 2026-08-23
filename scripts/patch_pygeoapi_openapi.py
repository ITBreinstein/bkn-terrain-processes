#!/usr/bin/env python3
"""Align pygeoapi 0.23.4's generated OpenAPI with the public product API.

pygeoapi already implements process-list limiting and unknown-process 404
responses. This module makes those behaviours, the conformance and process-list
response bodies, and the public process's synchronous execution responses
explicit in the generated OpenAPI document. It also removes generic framework
operations and presentation metadata that this synchronous product does not
offer.

The references are pinned to the official OGC API Processes 1.0 schemas. This
compatibility pass must be removed when the selected pygeoapi release generates
equivalent descriptions itself.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from bkn_terrain_processes import __version__
from bkn_terrain_processes.process_contract import PROCESS_METADATA

SCHEMA_BASE = "https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas"
PUBLIC_PROCESS_PATH = "/processes/bgt-land-cover-summary"
PUBLIC_EXECUTION_PATH = "/processes/bgt-land-cover-summary/execution"
SERVICE_TAG = "Service information"


def _json_response(description: str, schema_path: str) -> dict[str, Any]:
    """Build an OpenAPI JSON response using the Processes 1.0 schema."""

    return {
        "description": description,
        "content": {"application/json": {"schema": {"$ref": f"{SCHEMA_BASE}/{schema_path}"}}},
    }


def _landing_page_response() -> dict[str, Any]:
    """Describe this service instead of pygeoapi's generic Bonn example."""
    return {
        "description": "Information about the BGT Land-cover Summary API.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["title", "description", "links"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "links": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["href", "rel", "type"],
                                "properties": {
                                    "href": {"type": "string", "format": "uri"},
                                    "rel": {"type": "string"},
                                    "type": {"type": "string"},
                                    "title": {"type": "string"},
                                    "hreflang": {"type": "string"},
                                },
                                "additionalProperties": True,
                            },
                        },
                    },
                    "additionalProperties": False,
                },
                "example": {
                    "title": "BGT Land-cover Summary API",
                    "description": (
                        "Synchronous prototype for calculating BKN-oriented land-cover proxies from PDOK BGT data."
                    ),
                    "links": [
                        {
                            "href": "http://localhost:5001/processes/bgt-land-cover-summary",
                            "rel": "http://www.opengis.net/def/rel/ogc/1.0/process-desc",
                            "type": "application/json",
                            "title": "BGT land-cover summary process",
                        }
                    ],
                },
            }
        },
    }


def _execution_request_schema() -> dict[str, Any]:
    """Describe only the execution members accepted by the public process."""
    input_definitions = PROCESS_METADATA["inputs"]
    input_properties = {name: deepcopy(definition["schema"]) for name, definition in input_definitions.items()}
    required_inputs = [name for name, definition in input_definitions.items() if definition.get("minOccurs", 0) > 0]

    return {
        "type": "object",
        "required": ["inputs"],
        "properties": {
            "inputs": {
                "type": "object",
                "required": required_inputs,
                "properties": input_properties,
                "additionalProperties": False,
            },
            "outputs": {
                "type": "object",
                "minProperties": 1,
                "properties": {
                    "summary": {
                        "type": "object",
                        "properties": {
                            "transmissionMode": {
                                "type": "string",
                                "enum": ["value"],
                                "default": "value",
                            },
                            "format": {
                                "type": "object",
                                "properties": {
                                    "mediaType": {
                                        "type": "string",
                                        "enum": ["application/json"],
                                        "default": "application/json",
                                    }
                                },
                                "additionalProperties": False,
                            },
                        },
                        "additionalProperties": False,
                    }
                },
                "additionalProperties": False,
            },
            "response": {
                "type": "string",
                "enum": ["raw", "document"],
                "default": "raw",
            },
        },
        "additionalProperties": False,
    }


def _rename_service_tag(document: dict[str, Any]) -> None:
    """Give pygeoapi's generic server group a user-facing name."""
    for tag in document.get("tags", []):
        if tag.get("name") == "server":
            tag["name"] = SERVICE_TAG

    for path_item in document.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            operation_tags = operation.get("tags", [])
            operation["tags"] = [SERVICE_TAG if tag == "server" else tag for tag in operation_tags]


def _remove_unused_tags(document: dict[str, Any]) -> None:
    """Remove top-level tags that no remaining operation uses."""
    used_tags = {
        tag
        for path_item in document.get("paths", {}).values()
        for operation in path_item.values()
        if isinstance(operation, dict)
        for tag in operation.get("tags", [])
    }
    document["tags"] = [tag for tag in document.get("tags", []) if tag.get("name") in used_tags]


def _patch_public_presentation(document: dict[str, Any]) -> None:
    """Limit the public document to this synchronous product API."""
    info = document.setdefault("info", {})
    info["version"] = __version__
    info.pop("contact", None)

    paths = document["paths"]
    paths.pop("/collections", None)
    for path in list(paths):
        if path == "/jobs" or path.startswith("/jobs/"):
            paths.pop(path)

    landing_page = paths.get("/", {}).get("get")
    if landing_page is not None:
        landing_page.setdefault("responses", {})["200"] = _landing_page_response()

    _rename_service_tag(document)
    _remove_unused_tags(document)


def patch_openapi_document(document: dict[str, Any], default_limit: int, maximum_limit: int) -> dict[str, Any]:
    """Patch the generated document in place and return it."""

    paths = document["paths"]

    paths["/conformance"]["get"]["responses"]["200"] = _json_response(
        "The OGC API conformance classes supported by this service.",
        "confClasses.yaml",
    )

    process_list = paths["/processes"]["get"]
    parameters = process_list.setdefault("parameters", [])
    if not any(parameter.get("name") == "limit" for parameter in parameters):
        parameters.append(
            {
                "name": "limit",
                "in": "query",
                "description": "Maximum number of process summaries to return.",
                "required": False,
                "schema": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": maximum_limit,
                    "default": default_limit,
                },
            }
        )

    process_list["responses"]["200"] = _json_response(
        "Information about the processes available from this service.",
        "processList.yaml",
    )

    not_found = _json_response(
        "The requested process does not exist.",
        "exception.yaml",
    )
    for path, path_item in paths.items():
        parts = path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "processes":
            path_item["get"]["responses"]["404"] = not_found

    execution = paths.get(PUBLIC_EXECUTION_PATH, {}).get("post")
    if execution is not None:
        execution["parameters"] = [
            parameter for parameter in execution.get("parameters", []) if parameter.get("name") != "Prefer"
        ]
        execution["requestBody"] = {
            "description": "Synchronous BGT land-cover summary request.",
            "required": True,
            "content": {
                "application/json": {
                    "schema": _execution_request_schema(),
                    "example": deepcopy(PROCESS_METADATA["example"]),
                }
            },
        }

        responses = execution["responses"]
        # The public process is synchronous on this branch. Advertising an
        # unimplemented 201 would violate OpenAPI implementation truthfulness;
        # the async implementation must restore it with the matching runtime.
        responses.pop("201", None)
        responses["400"] = _json_response(
            "The execution request does not match the process contract.",
            "exception.yaml",
        )

        success_content = responses.get("200", {}).get("content", {}).get("application/json")
        if success_content is not None and "schema" in success_content:
            raw_schema = deepcopy(success_content["schema"])
            success_content["schema"] = {
                "oneOf": [
                    raw_schema,
                    {
                        "type": "object",
                        "required": ["summary"],
                        "properties": {
                            "summary": {
                                "type": "object",
                                "required": ["value"],
                                "properties": {"value": deepcopy(raw_schema)},
                                "additionalProperties": False,
                            }
                        },
                        "additionalProperties": False,
                    },
                ]
            }

    if PUBLIC_PROCESS_PATH in paths:
        _patch_public_presentation(document)

    return document


def patch_openapi_file(openapi_path: Path, config_path: Path | None = None) -> None:
    """Read, patch and overwrite a generated OpenAPI YAML document."""

    default_limit = 10
    maximum_limit = 10
    if config_path is not None:
        with config_path.open(encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
        limits = config.get("server", {}).get("limits", {})
        default_limit = int(limits.get("default_items", default_limit))
        maximum_limit = int(limits.get("max_items", maximum_limit))

    with openapi_path.open(encoding="utf-8") as openapi_file:
        document = yaml.safe_load(openapi_file)

    patch_openapi_document(document, default_limit, maximum_limit)

    with openapi_path.open("w", encoding="utf-8") as openapi_file:
        yaml.safe_dump(document, openapi_file, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("openapi", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    patch_openapi_file(args.openapi, args.config)


if __name__ == "__main__":
    main()
