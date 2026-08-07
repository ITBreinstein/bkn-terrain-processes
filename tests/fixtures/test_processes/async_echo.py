"""Diagnostic processor used only for async integration testing.

It does no real calculation and is never registered in the public service.
It exercises job-manager wiring without making live PDOK calls.
"""

import logging
import time
from datetime import UTC, datetime

from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError

LOGGER = logging.getLogger(__name__)

MAX_DELAY_SECONDS = 60

PROCESS_METADATA = {
    "version": "0.1.0",
    "id": "async-echo",
    "title": "Asynchronous execution test fixture",
    "description": (
        "Integration-test process that sleeps for a configurable duration and returns a fixed message. "
        "It performs no real calculation and is not part of the public API."
    ),
    "keywords": ["diagnostic", "async", "job manager"],
    "jobControlOptions": ["sync-execute", "async-execute"],
    "outputTransmission": ["value"],
    "inputs": {
        "delay_seconds": {
            "title": "Delay",
            "description": "Seconds to sleep before returning.",
            "schema": {
                "type": "integer",
                "minimum": 0,
                "maximum": MAX_DELAY_SECONDS,
                "default": 5,
            },
            "minOccurs": 0,
            "maxOccurs": 1,
        }
    },
    "outputs": {
        "result": {
            "title": "Demo result",
            "description": "Fixed message plus start/finish timestamps.",
            "schema": {
                "type": "object",
                "required": [
                    "message",
                    "requested_delay_seconds",
                    "started_at",
                    "finished_at",
                ],
                "properties": {
                    "message": {"type": "string"},
                    "requested_delay_seconds": {"type": "integer"},
                    "started_at": {"type": "string", "format": "date-time"},
                    "finished_at": {"type": "string", "format": "date-time"},
                },
                "additionalProperties": False,
            },
        },
        "debug_log": {
            "title": "Debug log",
            "description": (
                "Step-by-step execution trace. Excluded from the default response; "
                "only returned when explicitly requested by name in the request's `outputs` field."
            ),
            "schema": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
    "example": {"inputs": {"delay_seconds": 5}},
}


class AsyncEchoProcessor(BaseProcessor):
    """No-op processor used only to exercise sync/async job-manager plumbing."""

    def __init__(self, processor_def):
        super().__init__(processor_def, PROCESS_METADATA)
        self.supports_outputs = True

    def execute(self, data, outputs=None):
        try:
            delay_seconds = int(data.get("delay_seconds", 5))
        except (TypeError, ValueError) as err:
            raise ProcessorExecuteError("delay_seconds must be an integer") from err

        if not 0 <= delay_seconds <= MAX_DELAY_SECONDS:
            raise ProcessorExecuteError(f"delay_seconds must be between 0 and {MAX_DELAY_SECONDS}")

        started_at = datetime.now(UTC)
        debug_log = ["received request", f"sleeping for {delay_seconds}s"]
        time.sleep(delay_seconds)
        debug_log.append("woke up")
        finished_at = datetime.now(UTC)
        debug_log.append("building result")

        result = {
            "message": "async-echo completed",
            "requested_delay_seconds": delay_seconds,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
        }

        # pygeoapi's document-response wrapping (as also seen in its own
        # hello_world.py example) only handles execute() returning one
        # {"id": ..., "value": ...} dict, so a request naming both outputs
        # cannot get both back at once; debug_log wins if explicitly named.
        produced_output = {}
        if outputs and "debug_log" in outputs:
            produced_output = {"id": "debug_log", "value": debug_log}
        elif not outputs or "result" in outputs:
            produced_output = {"id": "result", "value": result}

        return "application/json", produced_output

    def __repr__(self):
        return f"<AsyncEchoProcessor> {self.name}"
