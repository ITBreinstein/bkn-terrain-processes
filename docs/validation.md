# Validation

Validation has three layers:

1. unit and schema tests for deterministic calculation and contract behaviour;
2. HTTP/container integration tests for the running service and job lifecycle;
3. OGC CITE/TEAM Engine and Geonovum checker runs against the deployed API.

The validator version, selected conformance classes, configuration, date and
complete output must be saved with release evidence. A global pygeoapi
conformance declaration is not proof that this process implements or has
tested a capability.

The acceptance baseline is OGC API Processes v1. The exact Geonovum v1 checker
invocation and optional classes, including Job List, must be confirmed with
Geonovum before the process contract is frozen.

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

Live PDOK execution demonstrates interoperability, but independently reviewed
reference cases provide repeatable calculation evidence. The public process
does not gain a hidden dummy-data mode for those tests.
