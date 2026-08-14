# CITE/TEAM Engine baseline — 2026-08-14

This is the first useful OGC API - Processes 1.0 CITE baseline for the
integration configuration. The CITE-compatible echo fixture was present, so
its results distinguish remaining API/schema findings from fixture setup
failures. The delivery target remains zero errors.

## Run metadata

- API source commit: `b26f1050c92d6bac851011f65c1b4a837d1a6191`
- Suite: `ogcapi-processes-1.0-1.3`
- TEAM Engine image: `ogccite/ets-ogcapi-processes10`
- Image digest: `sha256:8879e2d608e654d1f68aa94a2fd3b9bb1376f400737a2732ed32915a8e5211e8`
- Landing page: `http://api/`
- Echo process: `async-echo`
- Test all processes: selected
- Process-description limit: `2` (ignored because all processes were selected)
- Execution time: `2026-08-14T11:20:17Z` to `2026-08-14T11:20:20Z`

## Results

| Test group | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Core | 39 | 4 | 2 |
| OGC Process Description | 5 | 0 | 2 |
| Job List | 2 | 0 | 0 |
| **Total** | **46** | **4** | **4** |

The preceding setup-limited run had 24 passes, 24 failures and 6 skips. Adding
the CITE-compatible echo contract resolved 20 failures and two skips without
changing the product process.

## Scope of the asynchronous evidence

The asynchronous tests execute only `async-echo` through the integration-only
TinyDB manager. They show that the shared pygeoapi routes and temporary job
manager can create, monitor and return results for that controlled process.
They do not prove asynchronous execution, persistent jobs or restart recovery
for `bgt-land-cover-summary`.

With the TinyDB manager enabled, pygeoapi currently advertises both
`sync-execute` and `async-execute` for every process in the integration service,
including `bgt-land-cover-summary`. Its own source metadata still declares only
`sync-execute`. This difference is a property of the test configuration and
must not be interpreted as a delivered product capability.

## Remaining findings

1. `testJobCreationInputRef` and `testJobCreationInputValidation` execute
   successfully and return the expected message, but CITE reports that the
   response body matches more than one `oneOf` schema branch. Investigate the
   generated OpenAPI execution-response alternatives and the CITE v1 schema
   validator before assigning the defect to either implementation.
2. `testJobCreationSuccessAsync` receives a running job-status document whose
   `finished` property is `null`. CITE's v1 schema does not permit that value.
   Investigate pygeoapi's runtime status representation and documented schema.
3. `testJobResultsExceptionResultsNotReady` receives no exception document of
   type `result-not-ready` when it requests results while the five-second echo
   job is still running. The runtime response does not meet the tested v1
   requirement.

The four skipped tests are conditional. Two cover array and bounding-box input
forms not offered by the echo fixture; two cover mixed-type process inputs and
outputs not offered by either tested process.

## Evidence

- `testng-results.xml` contains the complete per-test result and failure data.
- `earl-results.rdf` contains the machine-readable EARL assertions.
- `teamengine-log.xml` contains the submitted run settings and concise failure
  messages.
