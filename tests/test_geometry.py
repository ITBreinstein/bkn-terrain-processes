"""Tests for buffer and overlap operations used by the calculation."""

import pytest
from shapely.geometry import box

from bkn_terrain_processes.classification import OVERLAP_PRIORITY
from bkn_terrain_processes.geometry import (
    build_analysis_buffers,
    category_percentages,
    mask_category_geometries,
    unpaved_surface_percentage,
)


def test_builds_inner_and_outer_buffers_in_square_metres():
    buffers = build_analysis_buffers(4.7534, 52.6324, 20, 30)

    assert buffers.inner_rd.area == pytest.approx(1254.62, rel=0.001)
    assert buffers.outer_rd.area == pytest.approx(2822.89, rel=0.001)
    assert len(buffers.outer_wgs_bounds) == 4


def test_priority_categories_do_not_double_count_overlap():
    merged = {
        "pand": box(0, 0, 2, 2),
        "weg": box(1, 0, 3, 2),
        "lage vegetatie": box(0, 0, 4, 2),
    }

    masked = mask_category_geometries(merged, OVERLAP_PRIORITY)

    assert masked["pand"].area == pytest.approx(4)
    assert masked["weg"].area == pytest.approx(2)
    assert masked["lage vegetatie"].area == pytest.approx(2)
    assert category_percentages(masked, buffer_area=8) == pytest.approx({"pand": 50, "weg": 25, "lage vegetatie": 25})


def test_unpaved_union_does_not_double_count_overlapping_unpaved_categories():
    masked = {
        "lage vegetatie": box(0, 0, 2, 2),
        "water": box(1, 0, 3, 2),
        "weg": box(3, 0, 4, 2),
    }

    assert unpaved_surface_percentage(masked, buffer_area=8) == pytest.approx(75)
