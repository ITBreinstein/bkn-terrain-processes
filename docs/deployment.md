# Deployment

The public deployment design is not yet frozen. It must use the same packaged
application tested in CI and must not depend on development bind mounts or the
integration-only TinyDB configuration.

Before first public deployment, document:

- image provenance and immutable version;
- public URL and reverse-proxy/TLS configuration;
- PostgreSQL, worker and result-storage topology;
- runtime configuration and secret injection;
- resource and concurrency limits;
- health/readiness behaviour;
- backup and restore procedure; and
- rollback procedure.
