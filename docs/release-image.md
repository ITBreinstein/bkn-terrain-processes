# Release image

## Purpose

The release image packages the synchronous BGT process, pygeoapi
configuration, OpenAPI compatibility correction and licence notices into one
portable artifact. It does not need the repository or a source-code mount at
runtime.

Build and start it with:

```bash
cp .env.example .env
docker compose --file compose.release.yml up --build --detach
```

The API is available at <http://localhost:5001>. Stop the stack with:

```bash
docker compose --file compose.release.yml down --volumes --remove-orphans
```

## Reproducible runtime boundary

The Dockerfile pins `geopython/pygeoapi:0.23.4` by immutable image digest. That
base supplies pygeoapi and the Python runtime dependencies used by the process.
Breinstein source and configuration are copied on top. Rebuilding a specific
Git commit therefore cannot silently move to a different base image under the
same tag.

The image version appears in `pyproject.toml`, the package, Docker labels and
Compose image names. Update these together when preparing another release.

## Runtime controls

The image itself runs as UID/GID `10001:10001` and listens on container port
8080. The release Compose file additionally:

- mounts no host source, configuration or persistent volume;
- makes the root filesystem read-only;
- provides a temporary, size-limited `/tmp` for generated API documents and
  process-manager scratch paths;
- drops all Linux capabilities; and
- prevents the process from gaining additional privileges.

CI starts this configuration, checks those properties and exercises the API's
discovery resources.

## Configuration

Copy `.env.example` to `.env` to change the host port, public server URL or
terms-of-service URL. `PYGEOAPI_SERVER_URL` must be the address that clients use
to reach the API because pygeoapi places it in generated links.

The canonical `config/pygeoapi.yml` is baked into the image. Changing it
requires rebuilding the image. The development Compose configuration mounts
the same local file so that release and development metadata cannot drift.

## What this does not provide

A self-contained image is a deployable artifact, not a complete production
service. An internet-facing deployment still needs decisions and ownership for:

- TLS termination and network exposure;
- authentication or access restrictions, if required;
- CPU, memory and request concurrency limits;
- central logging, monitoring and alerting;
- container-registry publication and vulnerability scanning;
- update and incident-response procedures; and
- availability and support expectations.

The current synchronous process stores no durable application state, so there
is no job database or application backup in this image.
