#!/usr/bin/env python3
"""Correct known pygeoapi 0.23.4 OpenAPI gaps for Processes discovery.

pygeoapi already implements process-list limiting and unknown-process 404
responses. This module makes those behaviours, the conformance and process-list
response bodies, and the public process's synchronous execution responses
explicit in the generated OpenAPI document.

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

SCHEMA_BASE = "https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/schemas"


def _json_response(description: str, schema_path: str) -> dict[str, Any]:
    """Build an OpenAPI JSON response using the Processes 1.0 schema."""

    return {
        "description": description,
        "content": {"application/json": {"schema": {"$ref": f"{SCHEMA_BASE}/{schema_path}"}}},
    }


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

    for path, path_item in paths.items():
        if path != "/processes/bgt-land-cover-summary/execution":
            continue

        execution = path_item.get("post")
        if execution is None:
            continue

        _remove_nonstandard_sync_preference(execution)

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

    return document


def _remove_nonstandard_sync_preference(operation: dict[str, Any]) -> None:
    """Replace pygeoapi's non-standard ``respond-sync`` preference token."""

    for parameter in operation.get("parameters", []):
        if parameter.get("name") != "Prefer":
            continue
        advertised_preferences = parameter.get("schema", {}).get("enum", [])
        if "respond-sync" in advertised_preferences:
            advertised_preferences.remove("respond-sync")
            if "respond-async" not in advertised_preferences:
                advertised_preferences.append("respond-async")
        return


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
