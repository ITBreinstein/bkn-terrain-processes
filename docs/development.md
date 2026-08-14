# Development workflow

## What GitHub checks automatically

The [CI workflow](../.github/workflows/ci.yml) runs for pull requests targeting
`main` and for pushes to `main`. Developers do not need to install or configure
GitHub Actions locally.

CI runs three jobs:

- `quality` checks formatting, linting, common security mistakes, tests,
  coverage, pygeoapi configuration and generated OpenAPI documents;
- `container-smoke` builds and starts the development container and checks that
  it publishes the expected discovery resources and BGT process, then compares
  Geonovum checker findings with the reviewed diagnostic baseline; and
- `live-point-baseline` checks one manually asserted water case and one varied
  urban case against live PDOK on pull requests. A manually started workflow
  checks all eight recorded locations.

Running the same checks locally is optional but recommended. It gives faster
feedback before a push; GitHub remains the shared result used when reviewing a
pull request.

## Prerequisites

Install:

- [Git](https://git-scm.com/downloads);
- [Docker](https://docs.docker.com/get-started/get-docker/) with Docker Compose;
  and
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python
  dependencies and checks.

These tools are available for Windows, macOS and Linux. WSL is supported but
not required. The repository selects Python 3.12 through `.python-version`;
`uv` can install and manage that Python version when needed. Conda and manual
virtual-environment activation are not required.

Run all commands below from the repository root.

## One-time project setup

Install the exact locked Python dependencies, including development tools:

```bash
uv sync --locked --all-groups
```

This creates a local `.venv`. Use `uv run ...` for project commands; activating
the environment is unnecessary.

Create the local environment file on macOS, Linux or WSL:

```bash
cp .env.example .env
```

In PowerShell, use:

```powershell
Copy-Item .env.example .env
```

The default API address is <http://localhost:5001>.

## Fast checks before pushing

Run the checks used by the CI `quality` job:

```bash
uv run ruff format --check src tests scripts
uv run ruff check src tests scripts
uv run bandit -r src scripts -c pyproject.toml
uv run pytest --cov=bkn_terrain_processes --cov-report=term-missing --cov-fail-under=30
```

The formatting check reports files that need formatting without changing them.
To apply the formatter, run:

```bash
uv run ruff format src tests scripts
```

The 30% coverage threshold protects the existing baseline from decreasing. It
is not the final test-coverage target. Feature branches should add tests for
the behaviour they introduce.

## Check live PDOK results

Run the same two cases used as the pull-request canary:

```bash
uv run python scripts/check_live_point_baseline.py \
  --case gouwzee-near-monnickergat \
  --case amsterdam-rembrandtpark-roundabout \
  --strict-historical
```

Strict mode makes any difference in the selected historical urban case fail
the pull-request check. Without it, the complete eight-case run tolerates up to
three isolated historical differences so local PDOK changes can be reviewed
without automatically being treated as an application-wide regression.

Run all eight recorded cases before a release, demonstration, or investigation:

```bash
uv run python scripts/check_live_point_baseline.py
```

GitHub's **Run workflow** action also runs the complete eight-case check. Live
PDOK checks are slower and can be affected by the upstream service, so they are
separate from deterministic unit tests and do not contribute to Python
coverage.

## Validate configuration and OpenAPI

Validate the normal development configuration and generate its OpenAPI
document:

```bash
uv run pygeoapi config validate --config config/pygeoapi.development.yml
uv run pygeoapi openapi generate --format yaml --output-file pygeoapi-openapi.yml config/pygeoapi.development.yml
uv run pygeoapi openapi validate pygeoapi-openapi.yml
```

The integration configuration refers to a test-only process under
`tests/fixtures`, so that directory must temporarily be added to Python's
module search path.

On macOS, Linux or WSL:

```bash
PYTHONPATH="$PWD/tests/fixtures" uv run pygeoapi config validate --config config/pygeoapi.integration.yml
PYTHONPATH="$PWD/tests/fixtures" uv run pygeoapi openapi generate --format yaml --output-file pygeoapi-openapi.yml config/pygeoapi.integration.yml
uv run pygeoapi openapi validate pygeoapi-openapi.yml
```

In PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path tests/fixtures).Path
uv run pygeoapi config validate --config config/pygeoapi.integration.yml
uv run pygeoapi openapi generate --format yaml --output-file pygeoapi-openapi.yml config/pygeoapi.integration.yml
Remove-Item Env:PYTHONPATH
uv run pygeoapi openapi validate pygeoapi-openapi.yml
```

The generated `pygeoapi-openapi.yml` is ignored by Git and may be overwritten
or deleted after validation.

## Start and smoke-test the normal API

Build and start the development container:

```bash
docker compose config --quiet
docker compose up --build --detach
docker compose ps
```

Changes under `src/bkn_terrain_processes` are mounted read-only into the
development container. Restart the API after Python or configuration changes:

```bash
docker compose restart api
```

Check that the running container exposes the landing page, conformance
declaration, generated OpenAPI document, process list and
`bgt-land-cover-summary` process description:

```bash
python3 scripts/smoke_discovery.py --base-url http://localhost:5001 --wait-seconds 60
```

On Windows, `python` may be used instead of `python3` if that is the available
command. The smoke test does not execute the process or contact PDOK.

If the smoke test fails, inspect the service logs:

```bash
docker compose logs api
```

Stop the development stack when it is no longer needed:

```bash
docker compose down --volumes --remove-orphans
```

## Start the integration configuration

```bash
docker compose -f compose.yml -f compose.integration.yml up --build --detach
```

This configuration uses disposable TinyDB storage and exposes `async-echo`.
It must not be deployed publicly and does not demonstrate persistent jobs or
callbacks.

## Branch and review policy

Use short-lived `feat/`, `fix/`, `test/`, `docs/`, `build/`, `chore/` or
`refactor/` branches. Branches describe a coherent change, not the developer
working on it. Open a pull request into `main` to start CI, describe how the
change was verified and ask for review where practical.

Keep `main` runnable. The accepted public process schema, classification
method, callback security and deployment architecture require review by their
workstream owners.
