# Geonovum checker baseline

The automated check uses `@geonovum/ogc-checker` version `1.1.0`. That checker
release only provides the draft OGC API - Processes `2.0.0` ruleset; it does
not provide a Processes `1.0.0` ruleset. OGC CITE/TEAM Engine separately tests
the approved Processes 1.0 specification.

Run the normal API with an explicit loopback address:

```bash
PYGEOAPI_SERVER_URL=http://127.0.0.1:5001 \
docker compose up --build --detach --force-recreate api
```

Compare a complete checker run with the reviewed baseline:

```bash
python3 scripts/check_geonovum_baseline.py
```

The script makes up to five attempts after command, network or schema-resolution
failures. If it cannot obtain a complete report, it exits with an operational
error instead of treating incomplete results as API diagnostics.

The comparison fails when a diagnostic is added, removed or changed. A removed
diagnostic represents an improvement, but the baseline must be deliberately
updated in the same pull request so that the resolved fault cannot silently
return:

```bash
python3 scripts/check_geonovum_baseline.py --update-baseline
```

Never use `--update-baseline` in CI. Review every baseline change and explain
the added, resolved or changed diagnostic in the pull request. The delivery
target remains an empty diagnostic list.
