# Changelog

Notable changes to the prototype are recorded here. Git history contains the
complete development record.

## Unreleased

### Documentation

- Reframe the repository as an independent synchronous prototype.
- Document implemented capabilities, known limitations and validation
  boundaries explicitly.
- Limit generated OpenAPI and Redoc documentation to the public synchronous
  process and service-information resources.

### Added

- Add a self-contained release image with no source mounts.
- Run the release container as a non-root user with a read-only filesystem and
  reduced Linux privileges.
- Validate release configuration, startup and isolation properties in CI.

## 0.2.0

### Added

- Cursor-based pagination of PDOK BGT collections with a fixed retrieval time.
- Explicit input parsing and error responses for the coordinate/radius
  contract.
- OGC API Processes raw and document response formatting for the synchronous
  process.
- Unit, schema, HTTP contract, container smoke and live-PDOK regression checks.
- Stored Geonovum checker and OGC CITE/TEAM Engine baseline evidence.

### Changed

- Separate the Breinstein calculation package from pygeoapi framework code.
- Restrict the public process description and runtime to the implemented
  synchronous capability.

### Known limitations

- Geometry inputs, referenced inputs, persistent asynchronous jobs and OGC
  subscriber callbacks are not implemented.
- The repository does not claim complete OGC API Processes conformance.
