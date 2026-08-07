# BKN Terrain Processes

OGC API Processes service for calculating BKN-oriented land-cover summaries
from Dutch BGT features retrieved through PDOK.

The output describes land-cover proxies. It is not an official Basiskwaliteit
Natuur assessment, does not measure vegetation height or tree-canopy volume,
and does not replace ecological expertise or municipal decision-making.

## Development status

This repository is the development and delivery repository for Geonovum nLDT
Testbed 2026 Phase 2, Adoption Topic 1. The current baseline preserves the
working synchronous point calculation while the awarded process contract is
implemented.

| Capability | Status |
| --- | --- |
| Live PDOK BGT retrieval and two-radius point summary | Implemented baseline |
| OGC process description and synchronous execution | Implemented baseline |
| GeoJSON Point, Polygon and MultiPolygon contract | Planned |
| Independently verified reference cases | Planned |
| Persistent asynchronous jobs and results | Planned |
| Standard subscriber callbacks | Planned |
| OGC CITE and Geonovum v1 zero-error evidence | Planned |
| Public deployment and six-month operation | Planned |

The complete delivery commitments and their current status are tracked in
[docs/delivery-requirements.md](docs/delivery-requirements.md).

## Requirements

- Docker Engine or Docker Desktop with Compose; and
- Git.

Python 3.12 and [uv](https://docs.astral.sh/uv/) are additionally required to
run the test suite directly on the host.

## Start the development API

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

The API is available at <http://localhost:5001> by default.

Useful resources:

- landing page: <http://localhost:5001/>;
- conformance declaration: <http://localhost:5001/conformance>;
- process list: <http://localhost:5001/processes>;
- process description: <http://localhost:5001/processes/bgt-land-cover-summary>;
- OpenAPI document: <http://localhost:5001/openapi>.

## Execute the current baseline

```bash
curl -sS -X POST \
  http://localhost:5001/processes/bgt-land-cover-summary/execution \
  -H 'Content-Type: application/json' \
  --data @examples/current-point-request.json \
  | python3 -m json.tool
```

The current request shape is retained only as a working baseline. It will be
replaced by the awarded `analysis_geometry` contract.

## Run checks

```bash
uv sync --locked --all-groups
uv run ruff format --check src tests scripts
uv run ruff check src tests scripts
uv run bandit -r src scripts -c pyproject.toml
uv run pytest --cov=bkn_terrain_processes --cov-report=term-missing
```

## Integration-only async diagnostic

The public development configuration exposes only the BGT process. To test
pygeoapi job-manager wiring with a predictable process, use the integration
override:

```bash
docker compose -f compose.yml -f compose.integration.yml up --build -d
```

This adds `async-echo`, a diagnostic fixture under `tests/fixtures`. Its result
is not product or conformance evidence, and it must not be enabled in public
deployments.

## Documentation

- [Architecture](docs/architecture.md)
- [Development workflow](docs/development.md)
- [Delivery requirements](docs/delivery-requirements.md)
- [Validation](docs/validation.md)
- [Security policy](SECURITY.md)

## Licence and source data

The software is released under the [MIT License](LICENSE). BGT source data is
retrieved from PDOK; source-data licensing and attribution are recorded with
the published reference package and outputs where applicable.
