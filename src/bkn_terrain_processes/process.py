"""Expose the BGT terrain calculation through pygeoapi."""

import logging
from collections.abc import Mapping

from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError

from .inputs import InvalidInputError, parse_analysis_request
from .process_contract import PROCESS_METADATA, SUMMARY_SCHEMA
from .terrain_analysis import get_terrain_analysis_nl

LOGGER = logging.getLogger(__name__)

# Keep these names available from the historical adapter module. Existing
# integrations and tests may import the published contract from here.
__all__ = ["BgtLandCoverSummaryProcessor", "PROCESS_METADATA", "SUMMARY_SCHEMA"]


class BgtLandCoverSummaryProcessor(BaseProcessor):
    """Expose the standalone terrain calculation through pygeoapi."""

    def __init__(self, processor_def):
        super().__init__(processor_def, PROCESS_METADATA)
        self.supports_outputs = True

    def execute(self, data, outputs=None):
        if outputs is not None:
            if not isinstance(outputs, Mapping):
                raise ProcessorExecuteError("outputs must be an object")
            if not outputs:
                raise ProcessorExecuteError("outputs must request at least one output")
            unsupported_outputs = sorted(set(outputs) - {"summary"})
            if unsupported_outputs:
                raise ProcessorExecuteError(f"unsupported output: {unsupported_outputs[0]}")
            if "summary" in outputs:
                summary_request = outputs["summary"]
                if not isinstance(summary_request, Mapping):
                    raise ProcessorExecuteError("summary output options must be an object")
                if summary_request.get("transmissionMode", "value") != "value":
                    raise ProcessorExecuteError("summary supports only value transmission")
                output_format = summary_request.get("format", {})
                if not isinstance(output_format, Mapping):
                    raise ProcessorExecuteError("summary output format must be an object")
                if output_format.get("mediaType", "application/json") != "application/json":
                    raise ProcessorExecuteError("summary supports only application/json")
                unsupported_format_members = sorted(set(output_format) - {"mediaType"})
                if unsupported_format_members:
                    raise ProcessorExecuteError(
                        f"unsupported summary output format member: {unsupported_format_members[0]}"
                    )

        try:
            request = parse_analysis_request(data)
        except InvalidInputError as err:
            raise ProcessorExecuteError(str(err)) from err

        try:
            result = get_terrain_analysis_nl(
                request.latitude,
                request.longitude,
                inner_radius_m=request.inner_radius_m,
                outer_radius_m=request.outer_radius_m,
            )
        except (ValueError, LookupError, RuntimeError) as err:
            raise ProcessorExecuteError(str(err)) from err
        except Exception as err:
            LOGGER.exception("Unexpected terrain-analysis failure")
            raise ProcessorExecuteError("Terrain analysis failed unexpectedly") from err

        produced_output = {}
        if not outputs or "summary" in outputs:
            produced_output = {"id": "summary", "value": result}

        return "application/json", produced_output

    def __repr__(self):
        return f"<BgtLandCoverSummaryProcessor> {self.name}"
