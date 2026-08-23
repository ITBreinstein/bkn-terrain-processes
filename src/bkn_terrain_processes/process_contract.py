"""Public process metadata and JSON schemas for the BGT summary process."""

from .inputs import (
    DEFAULT_INNER_RADIUS_M,
    DEFAULT_OUTER_RADIUS_M,
    MAX_RADIUS_M,
    MIN_RADIUS_M,
)

PERCENTAGE_SCHEMA = {
    "type": "number",
    "minimum": 0,
    "maximum": 100,
}

BKN_AREA_SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["bkn_indicators", "supporting_land_cover"],
    "properties": {
        "bkn_indicators": {
            "type": "object",
            "required": [
                "low_vegetation_proxy_pct",
                "medium_vegetation_proxy_pct",
                "high_vegetation_proxy_pct",
                "water_surface_pct",
                "unpaved_surface_proxy_pct",
            ],
            "properties": {
                "low_vegetation_proxy_pct": PERCENTAGE_SCHEMA,
                "medium_vegetation_proxy_pct": PERCENTAGE_SCHEMA,
                "high_vegetation_proxy_pct": PERCENTAGE_SCHEMA,
                "water_surface_pct": PERCENTAGE_SCHEMA,
                "unpaved_surface_proxy_pct": PERCENTAGE_SCHEMA,
            },
            "additionalProperties": False,
        },
        "supporting_land_cover": {
            "type": "object",
            "required": [
                "unknown_vegetation_pct",
                "road_pct",
                "built_pct",
                "bgt_explicitly_unpaved_pct",
            ],
            "properties": {
                "unknown_vegetation_pct": PERCENTAGE_SCHEMA,
                "road_pct": PERCENTAGE_SCHEMA,
                "built_pct": PERCENTAGE_SCHEMA,
                "bgt_explicitly_unpaved_pct": PERCENTAGE_SCHEMA,
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}

SUMMARY_SCHEMA = {
    "type": "object",
    "required": [
        "process",
        "source",
        "input",
        "is_partial",
        "fetch_failures",
        "classification",
        "timing_seconds",
        "completed_at",
        "within_inner_radius",
        "within_outer_radius",
    ],
    "properties": {
        "process": {
            "type": "object",
            "required": ["name", "algorithm_version"],
            "properties": {
                "name": {"type": "string"},
                "algorithm_version": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "source": {
            "type": "object",
            "required": ["name", "retrieved_at", "collections", "feature_counts", "page_counts"],
            "properties": {
                "name": {"type": "string"},
                "retrieved_at": {"type": "string", "format": "date-time"},
                "collections": {
                    "type": "object",
                    "additionalProperties": {"type": "string", "format": "uri"},
                },
                "feature_counts": {
                    "type": "object",
                    "additionalProperties": {"type": "integer", "minimum": 0},
                },
                "page_counts": {
                    "type": "object",
                    "additionalProperties": {"type": "integer", "minimum": 1},
                },
            },
            "additionalProperties": False,
        },
        "input": {
            "type": "object",
            "required": [
                "latitude",
                "longitude",
                "inner_radius_m",
                "outer_radius_m",
            ],
            "properties": {
                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                "longitude": {
                    "type": "number",
                    "minimum": -180,
                    "maximum": 180,
                },
                "inner_radius_m": {
                    "type": "integer",
                    "minimum": MIN_RADIUS_M,
                    "maximum": MAX_RADIUS_M,
                },
                "outer_radius_m": {
                    "type": "integer",
                    "minimum": MIN_RADIUS_M,
                    "maximum": MAX_RADIUS_M,
                },
            },
            "additionalProperties": False,
        },
        "is_partial": {"type": "boolean"},
        "fetch_failures": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "classification": {
            "type": "object",
            "required": [
                "is_official_standard",
                "method",
                "unpaved_surface_definition",
                "unknown_vegetation_types",
                "overlap_priority",
            ],
            "properties": {
                "is_official_standard": {"type": "boolean"},
                "method": {"type": "string"},
                "unpaved_surface_definition": {"type": "string"},
                "unknown_vegetation_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                },
                "overlap_priority": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                },
            },
            "additionalProperties": False,
        },
        "timing_seconds": {
            "type": "object",
            "required": ["by_collection", "total"],
            "properties": {
                "by_collection": {
                    "type": "object",
                    "additionalProperties": {"type": "number", "minimum": 0},
                },
                "total": {"type": "number", "minimum": 0},
            },
            "additionalProperties": False,
        },
        "completed_at": {"type": "string", "format": "date-time"},
        "within_inner_radius": BKN_AREA_SUMMARY_SCHEMA,
        "within_outer_radius": BKN_AREA_SUMMARY_SCHEMA,
    },
    "additionalProperties": False,
}

PROCESS_METADATA = {
    "version": "0.2.0",
    "id": "bgt-land-cover-summary",
    "title": "BKN-oriented BGT land-cover summary",
    "description": (
        "Calculates BKN-oriented land-cover proxies within two circular radii "
        "around a WGS 84 coordinate using live PDOK BGT data. The results do "
        "not directly measure vegetation height or tree-canopy volume and are "
        "not an official BKN assessment."
    ),
    "keywords": ["BKN", "BGT", "PDOK", "land cover", "Netherlands"],
    "jobControlOptions": ["sync-execute"],
    "outputTransmission": ["value"],
    "links": [
        {
            "type": "text/html",
            "rel": "about",
            "title": "PDOK BGT API",
            "href": "https://api.pdok.nl/lv/bgt/ogc/v1",
            "hreflang": "nl",
        },
        {
            "type": "text/html",
            "rel": "about",
            "title": "Basiskwaliteit Natuur toolbox",
            "href": "https://www.samenvoorbiodiversiteit.nl/toolbox/basiskwaliteitnatuur",
            "hreflang": "nl",
        },
    ],
    "inputs": {
        "latitude": {
            "title": "Latitude",
            "description": "WGS 84 latitude in decimal degrees.",
            "schema": {"type": "number", "minimum": -90, "maximum": 90},
            "minOccurs": 1,
            "maxOccurs": 1,
        },
        "longitude": {
            "title": "Longitude",
            "description": "WGS 84 longitude in decimal degrees.",
            "schema": {"type": "number", "minimum": -180, "maximum": 180},
            "minOccurs": 1,
            "maxOccurs": 1,
        },
        "inner_radius_m": {
            "title": "Inner radius",
            "description": "Radius in metres for the first complete circular area.",
            "schema": {
                "type": "integer",
                "minimum": MIN_RADIUS_M,
                "maximum": MAX_RADIUS_M,
                "default": DEFAULT_INNER_RADIUS_M,
            },
            "minOccurs": 0,
            "maxOccurs": 1,
        },
        "outer_radius_m": {
            "title": "Outer radius",
            "description": "Radius in metres for the second complete circular area.",
            "schema": {
                "type": "integer",
                "minimum": MIN_RADIUS_M,
                "maximum": MAX_RADIUS_M,
                "default": DEFAULT_OUTER_RADIUS_M,
            },
            "minOccurs": 0,
            "maxOccurs": 1,
        },
    },
    "outputs": {
        "summary": {
            "title": "BKN-oriented BGT land-cover summary",
            "description": ("Percentages, provenance, source diagnostics and execution timings."),
            "schema": {
                "contentMediaType": "application/json",
                **SUMMARY_SCHEMA,
            },
        }
    },
    "example": {
        "inputs": {
            "latitude": 52.6324,
            "longitude": 4.7534,
            "inner_radius_m": 300,
            "outer_radius_m": 500,
        }
    },
}
