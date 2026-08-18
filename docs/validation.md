# Validation

Validation has complementary layers. No single linter or validator proves OGC
API Processes compliance:

| Check | What it verifies | Important limit |
| --- | --- | --- |
| Ruff and Bandit | Selected source formatting, quality and security patterns | They do not execute the API or assess OGC semantics. |
| Pytest | Our functions, processor boundary and controlled failures | Most tests import Python directly rather than calling the running HTTP service. |
| pygeoapi config/OpenAPI validation | Configuration, processor imports, document generation and basic OpenAPI structure | A structurally valid document may still disagree with runtime behaviour. |
| Discovery smoke test | A clean container starts and serves the expected discovery resources | It deliberately does not execute the terrain process. |
| Geonovum checker | Static OGC rules applied to the generated `/openapi?f=json` document | It cannot observe input coercion, actual response bodies or terrain results. |
| CITE/TEAM Engine | Runtime tests of the integration service; execution cases use `async-echo` | It does not execute `bgt-land-cover-summary` or prove its calculation/job behaviour. |
| Live point baseline | The calculation function communicates with PDOK and preserves selected point outputs | It bypasses HTTP and six expectations are historical rather than independently calculated. |
| Product HTTP tests | Exact requests, statuses, headers and bodies of the real terrain process | This layer is still being built and must grow with the public contract. |

The validator version, selected conformance classes, configuration, date and
complete output must be saved with release evidence. A global pygeoapi
conformance declaration is not proof that this process implements or has
tested a capability.

The normative baseline is OGC API - Processes 1.0. CITE/TEAM Engine, the
Processes `1.0.0` profile in Geonovum checker package `1.2.0`, and product HTTP
tests provide different parts of the evidence. The final selection of optional
conformance classes must be confirmed with Geonovum before the process
contract is frozen.

## OGC CITE/TEAM Engine

Run the OGC API - Processes 1.0 CITE suite locally before a pull request that
changes the HTTP API, process descriptions, execution behaviour, jobs or the
pygeoapi configuration. Documentation-only and other unrelated pull requests
do not require a new run.

Start the API with its integration-only configuration. `http://api` is the
address by which another container on the Compose network can reach it:

```bash
PYGEOAPI_SERVER_URL=http://api \
docker compose \
  -f compose.yml \
  -f compose.integration.yml \
  up --build --detach
```

Start TEAM Engine on the same Docker network:

```bash
docker run --detach \
  --rm \
  --name ogc-processes-teamengine \
  --network bkn-terrain-processes_default \
  --publish 127.0.0.1:8081:8080 \
  ogccite/ets-ogcapi-processes10
```

Open <http://localhost:8081/teamengine/> and sign in with username `ogctest`
and password `ogctest`. Create an OGC API - Processes 1.0 session with:

- landing page: `http://api/`;
- echo process identifier: `async-echo`;
- test all processes: selected.

The echo identifier is exact: `async-echo`, not `asynch-echo`. The fixture is
available only through `compose.integration.yml` and is not part of the public
service.

The fixture exposes the plain string input/output pair used by CITE and the
optional `pause` input used by its results-not-ready test. It performs no
terrain calculation and does not contact PDOK.

The integration-only TinyDB manager may cause pygeoapi to advertise
asynchronous execution for all processes in this test service. CITE's async
execution results apply to `async-echo`; they are not evidence that the terrain
process has production-ready asynchronous execution or persistent job storage.
Selecting “test all processes” broadens discovery/process-description checks;
it does not make CITE invent domain inputs for terrain execution. The terrain
process therefore needs its own black-box HTTP contract and lifecycle tests.

After a valid run, copy the session directory from the container. Replace
`s0001` with the session identifier shown by TEAM Engine:

```bash
docker cp \
  ogc-processes-teamengine:/root/te_base/users/ogctest/s0001 \
  /tmp/cite-teamengine-s0001
```

Retain only the evidence described in
[`validation/cite-teamengine/README.md`](../validation/cite-teamengine/README.md).
Do not commit TEAM Engine's complete generated HTML and JavaScript tree.

Record the tested API commit and container-image digest with every accepted
baseline:

```bash
git rev-parse HEAD
docker image inspect ogccite/ets-ogcapi-processes10 \
  --format '{{index .RepoDigests 0}}'
```

Stop the validation environment after the run:

```bash
docker stop ogc-processes-teamengine
docker compose -f compose.yml -f compose.integration.yml down
docker compose up --detach
```

The final command restores the normal development API, whose generated links
use `http://localhost:5001`.

TEAM Engine remains a manual pre-merge check for now. Its REST interface could
be automated later, but only after the test fixture and baseline are stable.
GitHub CI will run the lighter Geonovum checker and verify its exact diagnostic
baseline instead.

## Geonovum checker

The CI workflow runs `@geonovum/ogc-checker` version `1.2.0` with its OGC API -
Processes `1.0.0` profile against the normal API's `/openapi?f=json` document.
The current profile applies Core, Job List, JSON and OGC Process Description
rules. Its seven baseline diagnostics are all missing optional Job List query
parameters; the normal service does not currently declare Job List. The
recorded rulesets do not include the separate OpenAPI 3.0 conformance class,
even though the service currently declares it.

The Geonovum checker is a static OpenAPI check. A zero-diagnostic result for a
selected ruleset would still not prove that the running processor rejects the
right input or returns the documented body. CITE provides runtime server
evidence through the echo fixture, while product HTTP tests must close the
terrain-specific gap.

The checker runs for pull requests and manually started workflows. The runner
retries explicit schema-download failures and then compares every stable
diagnostic field with the reviewed baseline. Added and changed diagnostics fail
as regressions. Removed diagnostics also require a reviewed baseline update so
that a resolved issue cannot silently return. The deterministic quality and
container smoke checks still run again after a merge to `main`, but the
network-dependent checker is not repeated for an identical squash-merged tree.
See
[`validation/geonovum/README.md`](../validation/geonovum/README.md) for the
commands and update policy.

Live PDOK execution demonstrates interoperability, but independently reviewed
reference cases provide repeatable calculation evidence. The public process
does not gain a hidden dummy-data mode for those tests.
