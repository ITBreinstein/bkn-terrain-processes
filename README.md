# BGT Land-cover Summary API

A synchronous OGC API Processes prototype that summarises selected land-cover
categories around a Dutch coordinate. The calculation retrieves current BGT
features through PDOK and reports percentages for two circular areas.

The categories are application-defined ecological proxies. The result is not
an official Basiskwaliteit Natuur (BKN) assessment and does not replace source
data review or ecological expertise.

## Project status

This repository began as technical exploration for Breinstein's proposal for
Geonovum nLDT Testbed 2026 Phase 2, Adoption Topic 1. Breinstein was assigned a
different testbed topic, so this project is not a Geonovum deliverable and has
not been certified or endorsed by Geonovum.

Breinstein publishes it as an independent prototype and technical reference.
Its complete development history is retained intentionally.

| Capability | Status |
| --- | --- |
| Live, paginated PDOK BGT retrieval | Implemented |
| Latitude/longitude input with two circular radii | Implemented |
| Synchronous OGC API Processes execution | Implemented |
| Raw and document response forms | Implemented |
| Automated source, schema and HTTP contract tests | Implemented |
| GeoJSON Point, Polygon or MultiPolygon input | Not implemented |
| Referenced input files | Not implemented |
| Asynchronous terrain jobs and persistent results | Not implemented |
| OGC subscriber callbacks | Not implemented |
| Full OGC API Processes conformance | Not claimed |
| Production deployment or support | Not provided |

## What the prototype demonstrates

- keeping calculation code separate from pygeoapi's HTTP and process-manager
  integration;
- buffering WGS 84 coordinates in the Dutch RD New projected coordinate
  system (EPSG:28992);
- following PDOK cursor pagination and requesting a consistent point in time;
- exposing an explicit synchronous process contract and rejecting unsupported
  subscriber options;
- returning a single JSON output in OGC API Processes raw or document form;
- testing calculation, input validation, generated API descriptions and the
  running HTTP service at different layers; and
- preserving incomplete conformance-check results with their limitations
  instead of presenting them as certification.

## Requirements

- Docker Engine or Docker Desktop with Compose; and
- Git.

Python 3.12 and [uv](https://docs.astral.sh/uv/) are additionally required to
run the checks directly on the host.

## Start the API locally

```bash
cp .env.example .env
docker compose up --build --detach
docker compose ps
```

The API is available at <http://localhost:5001> by default.

Useful resources:

- landing page: <http://localhost:5001/>;
- conformance declaration: <http://localhost:5001/conformance>;
- process list: <http://localhost:5001/processes>;
- process description: <http://localhost:5001/processes/bgt-land-cover-summary>;
- OpenAPI document: <http://localhost:5001/openapi>.

## Execute the process

```bash
curl -sS -X POST \
  http://localhost:5001/processes/bgt-land-cover-summary/execution \
  -H 'Content-Type: application/json' \
  --data @examples/current-point-request.json \
  | python3 -m json.tool
```

The request contains WGS 84 latitude and longitude values and two radii in
metres. The response includes percentages for both circular areas, source and
collection counts, timing information and the classification method used.
Because the process queries live PDOK data, its exact result can change as the
source registration changes.

## Run the checks

```bash
uv sync --locked --all-groups
uv run ruff format --check src tests scripts
uv run ruff check src tests scripts
uv run bandit -r src scripts -c pyproject.toml
uv run pytest --cov=bkn_terrain_processes --cov-report=term-missing --cov-fail-under=70
```

The repository also contains a container smoke check, black-box tests of the
public synchronous process, historical live-PDOK regression cases and stored
output from the Geonovum checker and OGC CITE/TEAM Engine. See
[Validation](docs/validation.md) before interpreting those results.

## Integration-only validation fixture

The normal configuration exposes only the BGT process. The integration
configuration adds `async-echo`, a predictable CITE-compatible process backed
by disposable TinyDB storage:

```bash
docker compose -f compose.yml -f compose.integration.yml up --build --detach
```

This fixture lets CITE exercise generic synchronous and asynchronous pygeoapi
routes without terrain-specific inputs or live PDOK data. It is not part of
the product API and does not prove asynchronous execution of the terrain
process.

## Known limitations

- Inputs are separate scalar coordinate and radius values; GeoJSON geometry
  and referenced inputs are not supported.
- The terrain process is synchronous only. There is no persistent job store,
  restart recovery, job dismissal or subscriber delivery.
- The application-defined BGT-to-category mapping has not been independently
  validated as a BKN method.
- BGT `relatieveHoogteligging` is not used, so geometries at different relative
  heights can be combined by the current overlap-removal logic.
- Six of the eight live point baselines are historical regression values, not
  independently calculated ground truth.
- The Compose setup is a development environment with bind-mounted source; it
  is not a self-contained production image.

## Documentation

- [Architecture](docs/architecture.md)
- [Development workflow](docs/development.md)
- [Validation and evidence boundaries](docs/validation.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Contributors](CONTRIBUTORS.md)

## Licence and source data

Breinstein's source code is released under the [MIT License](LICENSE).
Licences and copyright notices for included third-party software are recorded
in [Third-party notices](THIRD_PARTY_NOTICES.md).

The process retrieves Basisregistratie Grootschalige Topografie (BGT) data
from the [PDOK BGT OGC API](https://api.pdok.nl/lv/bgt/ogc/v1?f=html&lang=en).
The dataset provider is Kadaster (LV-BGT); PDOK publishes the service under the
[CC0 1.0 public-domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
