"""Coordinate transforms, circular buffers, clipping, and overlap handling."""

import logging
from dataclasses import dataclass

import pyproj
from shapely.geometry import Point
from shapely.ops import transform, unary_union
from shapely.validation import make_valid

from .classification import BKN_UNPAVED_CATEGORIES

logger = logging.getLogger(__name__)

to_rd = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True).transform
to_wgs = pyproj.Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True).transform


@dataclass(frozen=True)
class AnalysisBuffers:
    """Inner and outer circular analysis areas in the working CRS."""

    inner_rd: object
    outer_rd: object
    outer_wgs_bounds: tuple[float, float, float, float]


def build_analysis_buffers(
    longitude: float,
    latitude: float,
    inner_radius_m: int,
    outer_radius_m: int,
) -> AnalysisBuffers:
    """Build both circular analysis areas around a WGS 84 coordinate."""
    station_rd = to_rd(longitude, latitude)
    outer_rd = Point(station_rd).buffer(outer_radius_m)
    inner_rd = Point(station_rd).buffer(inner_radius_m)
    outer_wgs_bounds = transform(to_wgs, outer_rd).bounds
    return AnalysisBuffers(inner_rd=inner_rd, outer_rd=outer_rd, outer_wgs_bounds=outer_wgs_bounds)


def clip_feature_to_buffer(geometry, buffer_rd):
    """Clip a WGS 84 source geometry and return the valid result in WGS 84."""
    try:
        geometry_rd = transform(to_rd, geometry)
        clipped_geometry = geometry_rd.intersection(buffer_rd)

        if not clipped_geometry.is_valid:
            clipped_geometry = make_valid(clipped_geometry)

        if clipped_geometry.is_empty:
            return None

        return transform(to_wgs, clipped_geometry)

    except ValueError as error:
        logger.debug("Geometry value error in clip_feature_to_buffer: %s", error)
        return None

    except TypeError as error:
        logger.debug("Geometry type error in clip_feature_to_buffer: %s", error)
        return None


def to_rd_geometry(geometry):
    """Transform a WGS 84 geometry to the analysis CRS."""
    return transform(to_rd, geometry)


def merge_category_geometries(category_geometries: dict[str, list]) -> dict[str, object | None]:
    """Merge all clipped parts belonging to each category."""
    merged = {}
    for category, geometries in category_geometries.items():
        if geometries:
            merged_geometry = unary_union(geometries)
            merged[category] = None if merged_geometry.is_empty else merged_geometry
        else:
            merged[category] = None
    return merged


def mask_category_geometries(
    merged_geometries: dict[str, object | None],
    priority_order: list[str],
) -> dict[str, object | None]:
    """Apply the calculation's existing priority masking without changing its semantics."""
    masked_geometries = {}
    covered_area = None

    for category in priority_order:
        if category in merged_geometries and merged_geometries[category]:
            if covered_area is None:
                masked_geometries[category] = merged_geometries[category]
            else:
                masked_geometries[category] = merged_geometries[category].difference(covered_area)

            if masked_geometries[category].is_empty:
                masked_geometries[category] = None
            else:
                covered_area = (
                    masked_geometries[category]
                    if covered_area is None
                    else covered_area.union(masked_geometries[category])
                )

    # Preserve the current algorithm: lower-priority categories are masked by
    # the accumulated priority area, but not by one another.
    for category, merged_geometry in merged_geometries.items():
        if category not in priority_order:
            if merged_geometry:
                if covered_area is None:
                    masked_geometries[category] = merged_geometry
                else:
                    masked_geometries[category] = merged_geometry.difference(covered_area)
                    if masked_geometries[category].is_empty:
                        masked_geometries[category] = None
            else:
                masked_geometries[category] = None

    return masked_geometries


def category_percentages(masked_geometries: dict[str, object | None], buffer_area: float) -> dict[str, float]:
    """Convert each non-empty category geometry to a percentage of the buffer."""
    return {
        category: (geometry.area / buffer_area) * 100 for category, geometry in masked_geometries.items() if geometry
    }


def unpaved_surface_percentage(masked_geometries: dict[str, object | None], buffer_area: float) -> float:
    """Calculate BKN-oriented unpaved surface without double-counting overlaps."""
    geometries = [
        geometry
        for category, geometry in masked_geometries.items()
        if category in BKN_UNPAVED_CATEGORIES and geometry is not None
    ]
    if not geometries:
        return 0.0
    return (unary_union(geometries).area / buffer_area) * 100
