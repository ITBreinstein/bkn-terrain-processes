"""pygeoapi process-manager compatibility for OGC Processes 1.0 results."""

from collections.abc import Mapping
from typing import Any

from pygeoapi.api import processes as processes_api
from pygeoapi.process.base import ProcessorExecuteError
from pygeoapi.process.manager.dummy import DummyManager
from pygeoapi.util import JobStatus, RequestedProcessExecutionMode, RequestedResponse

CALLBACK_CONFORMANCE_URI = "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/callback"


class UnsupportedExecutionOptionError(ProcessorExecuteError):
    """Reject an execution option that the public service does not offer."""

    http_status_code = 400
    ogc_exception_code = "InvalidParameterValue"

    def __init__(self, message: str):
        super().__init__(message, user_msg=message)


class InvalidProcessorResultError(ProcessorExecuteError):
    """Report a processor/manager contract defect without exposing internals."""

    def __init__(self):
        super().__init__(user_msg="process returned an invalid output")


def format_process_result(outputs: Any, requested_response: str) -> Any:
    """Translate pygeoapi's internal named output into an OGC 1.0 response."""

    if not isinstance(outputs, dict) or set(outputs) != {"id", "value"}:
        raise ValueError("processor result must contain exactly one id and value")

    output_id = outputs["id"]
    if not isinstance(output_id, str) or not output_id:
        raise ValueError("processor output id must be a non-empty string")

    value = outputs["value"]
    if requested_response == RequestedResponse.document.value:
        document_value = {"value": value} if isinstance(value, Mapping) else value
        return {output_id: document_value}
    return value


class OgcSynchronousManager(DummyManager):
    """Run processes synchronously and return OGC Processes 1.0 result bodies.

    pygeoapi 0.23.4's Dummy manager exposes its internal ``id``/``value``
    object for raw responses and puts that object in an ``outputs`` array for
    document responses. OGC API Processes 1.0 instead requires the output
    value itself for a single raw output, or a map keyed by output identifier
    for a document response.
    """

    def __init__(self, manager_def: dict):
        super().__init__(manager_def)

        # pygeoapi 0.23.4 declares Callback for every Processes service. The
        # current product has not implemented and tested that optional class.
        if CALLBACK_CONFORMANCE_URI in processes_api.CONFORMANCE_CLASSES:
            processes_api.CONFORMANCE_CLASSES.remove(CALLBACK_CONFORMANCE_URI)

    def execute_process(
        self,
        process_id,
        data_dict,
        execution_mode=None,
        requested_outputs=None,
        subscriber=None,
        requested_response=RequestedResponse.raw.value,
    ):
        if not isinstance(requested_response, str) or requested_response not in {
            RequestedResponse.raw.value,
            RequestedResponse.document.value,
        }:
            raise UnsupportedExecutionOptionError("response must be either raw or document")
        if subscriber is not None:
            raise UnsupportedExecutionOptionError("subscriber callbacks are not supported")

        # Always ask the parent for its unwrapped internal result. This class
        # owns the public raw/document representation below.
        job_id, mime_type, outputs, status, headers = super().execute_process(
            process_id,
            data_dict,
            execution_mode=execution_mode,
            requested_outputs=requested_outputs,
            subscriber=None,
            requested_response=RequestedResponse.raw.value,
        )

        # A sync-only process ignores ``Prefer: respond-async``. Do not claim
        # that another preference was applied when pygeoapi forces sync.
        if execution_mode == RequestedProcessExecutionMode.respond_async and headers is not None:
            headers.pop("Preference-Applied", None)

        if status == JobStatus.successful:
            try:
                outputs = format_process_result(outputs, requested_response)
            except ValueError as error:
                raise InvalidProcessorResultError() from error
        elif status == JobStatus.failed and isinstance(outputs, dict):
            # OGC's exception schema requires ``type``. Keep pygeoapi's code
            # and description as useful compatibility fields.
            outputs.setdefault("type", outputs.get("code", "NoApplicableCode"))

        return job_id, mime_type, outputs, status, headers
