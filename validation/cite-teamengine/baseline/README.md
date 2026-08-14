# CITE/TEAM Engine baseline — 2026-08-14

This is the first observed OGC API - Processes 1.0 CITE baseline for the
integration configuration. It records the current result accurately, but it is
not evidence of conformance: the integration-only echo fixture does not yet
satisfy all preconditions imposed by the test suite.

## Run metadata

- API commit: `1a82337411da413c885fb10324975ce232d0ac9c`
- Suite: `ogcapi-processes-1.0-1.3`
- TEAM Engine image: `ogccite/ets-ogcapi-processes10`
- Image digest: `sha256:8879e2d608e654d1f68aa94a2fd3b9bb1376f400737a2732ed32915a8e5211e8`
- Landing page: `http://api/`
- Echo process: `async-echo`
- Test all processes: selected
- Execution time: `2026-08-14T10:54:43Z` to `2026-08-14T10:55:15Z`

## Results

| Test group | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Core | 17 | 24 | 4 |
| OGC Process Description | 5 | 0 | 2 |
| Job List | 2 | 0 | 0 |
| **Total** | **24** | **24** | **6** |

## Interpretation

Seventeen Core failures report that the suite could not find a supported plain
string input. This is a limitation of the current `async-echo` test fixture,
not seventeen independent defects in the product process. The fixture also
lacks the CITE-specific `pause` input, causing the results-not-ready test to be
skipped.

The remaining failures expose areas to investigate after correcting the echo
fixture:

- referenced-input validation matches more than one alternative in the
  published request schema;
- one synchronous raw-output assertion fails without a detailed message;
- three asynchronous result responses contain a null `finished` value where
  the suite's schema does not allow it;
- one asynchronous raw result returned a not-yet-running exception page rather
  than the expected value; and
- the failed-job result test received HTTP 200 instead of the expected error
  response.

The two skipped mixed-type process-description tests are conditional: neither
tested process declares mixed-type inputs or outputs. Three further Core skips
cover input forms not offered by the echo fixture (array, bounding box and
binary).

The next baseline must be recorded after the integration echo fixture exposes
the plain string and `pause` inputs expected by this CITE suite. Only then can
the remaining result distinguish fixture setup from API conformance defects.

## Evidence

- `testng-results.xml` contains the complete per-test result and failure data.
- `earl-results.rdf` contains the machine-readable EARL assertions.
- `teamengine-log.xml` contains the submitted run settings and concise failure
  messages.
