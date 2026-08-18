"""WSGI boundary corrections for the public terrain process."""

from collections.abc import Mapping

from flask import jsonify, request
from pygeoapi.flask_app import APP

EXECUTION_PATH = "/processes/bgt-land-cover-summary/execution"
ALLOWED_EXECUTION_MEMBERS = {"inputs", "outputs", "response", "subscriber"}


def _invalid_execution_request(description: str):
    """Return the JSON exception shape used by the Processes API."""

    return (
        jsonify(
            {
                "type": "InvalidParameterValue",
                "code": "InvalidParameterValue",
                "description": description,
            }
        ),
        400,
    )


@APP.before_request
def validate_terrain_execution_document():
    """Reject malformed BGT execute documents before pygeoapi dereferences them.

    pygeoapi 0.23.4 assumes several execute members have the expected JSON
    types. Guarding this product route prevents valid-but-malformed JSON from
    becoming an HTML 500 response.
    """

    if request.method != "POST" or request.path != EXECUTION_PATH:
        return None

    document = request.get_json(silent=True)
    if document is None:
        # pygeoapi already reports missing and syntactically invalid JSON.
        return None
    if not isinstance(document, Mapping):
        return _invalid_execution_request("execution request must be an object")

    unknown_members = sorted(set(document) - ALLOWED_EXECUTION_MEMBERS)
    if unknown_members:
        return _invalid_execution_request(f"unsupported execution member: {unknown_members[0]}")

    if "response" in document:
        response_mode = document["response"]
        if not isinstance(response_mode, str) or response_mode not in {"raw", "document"}:
            return _invalid_execution_request("response must be either raw or document")

    if "subscriber" in document:
        return _invalid_execution_request("subscriber callbacks are not supported")

    return None
