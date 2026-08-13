# Live point baseline

This directory records eight Dutch point cases for checking the existing
calculation against live PDOK BGT data.

The cases use two evidence levels:

- `domain_assertion`: the Wadden Sea and Gouwzee locations are manually
  expected to return 100% water, with no non-water categories, for both the
  300 m and 500 m areas;
- `historical_baseline`: the other six expected summaries were produced by
  the current application against live PDOK on 13 August 2026.

Historical baselines protect the refactor from widespread accidental changes,
but they are not independently verified ground truth. An isolated difference
may mean that PDOK changed locally or that the application changed. The checker
therefore reports isolated historical differences as warnings and fails only
when at least four of the six historical cases differ. Any mismatch in a
manually stated water assertion fails immediately.

No PDOK source dataset is stored here. The checker deliberately retrieves the
current source data:

```bash
uv run python scripts/check_live_point_baseline.py
```

Use `--case CASE_ID` to check one location. The default numeric tolerance is
0.05 percentage point and can be overridden with `--tolerance`.

The command uses separate exit codes so CI output identifies the cause:

- `1`: a manual water assertion or at least four historical results differ;
- `2`: live PDOK data is unavailable or incomplete;
- `3`: the application raised an unexpected calculation error.

An isolated historical difference is reported as a warning and returns a
successful exit code.

Coordinates are stored in explicit `latitude` and `longitude` fields. GeoJSON
examples must reverse these into `[longitude, latitude]` order.

These cases can also supply example coordinates for the demo service. They do
not replace the promised independently verified QGIS reference package.
