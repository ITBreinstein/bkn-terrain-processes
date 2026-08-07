# Development workflow

## Set up Python checks

```bash
uv sync --locked --all-groups
uv run pytest
```

## Start the normal API

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f api
```

Changes under `src/bkn_terrain_processes` are mounted read-only into the
development container. Restart the API after Python or configuration changes:

```bash
docker compose restart api
```

## Start the integration configuration

```bash
docker compose -f compose.yml -f compose.integration.yml up --build -d
```

This configuration uses disposable TinyDB storage and exposes `async-echo`.
It must not be deployed publicly and does not demonstrate persistent jobs or
callbacks.

## Branch and review policy

Use short-lived `feat/`, `fix/`, `test/`, `docs/` or `chore/` branches. Link
each pull request to a delivery requirement or issue, describe verification,
and use squash merge. Keep `main` runnable and require CI before merge.

The accepted public process schema, classification method, callback security
and deployment architecture require review by their workstream owners.
