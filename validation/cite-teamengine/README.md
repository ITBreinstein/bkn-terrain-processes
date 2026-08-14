# OGC CITE/TEAM Engine evidence

This directory records the accepted OGC API - Processes 1.0 TEAM Engine
baseline. It is evidence of the observed implementation state, not permission
to ignore failures. The delivery target remains zero errors.

Keep the current baseline in `baseline/`. Updating the same directory lets Git
retain older baselines without accumulating a generated result tree for every
pull request.

Retain these files from a valid TEAM Engine session:

- `testng-results.xml`: complete pass, fail and skip results;
- `earl-results.rdf`: machine-readable EARL conformance evidence;
- `teamengine-log.xml`: submitted inputs, summary and concise failures; copied
  from the session's `log.xml`;
- `README.md`: human-readable run metadata and interpretation.

The baseline README must record:

- run date in `YYYY-MM-DD` form;
- full Git commit tested;
- TEAM Engine suite and version;
- Docker image digest;
- landing-page value;
- echo-process identifier;
- whether all processes were selected;
- pass, fail and skip totals by test group;
- each known failure or skip that affects interpretation.

Do not retain the complete `html/` or `result/` directories. They duplicate the
XML evidence with generated style sheets, JavaScript and one HTML page per
test. A reviewer can inspect `testng-results.xml`, `earl-results.rdf` and the
human-readable baseline summary instead.

A changed diagnostic set must be reviewed explicitly. A newly failing test is
a regression. A resolved failure requires the baseline evidence and summary to
be updated in the same pull request so that the failure cannot silently return.
