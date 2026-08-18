# Architecture

## Current development baseline

```text
client
  |
  v
pygeoapi development container
  |
  v
bkn_terrain_processes calculation
  |
  v
PDOK BGT OGC API Features
```

The normal development configuration exposes only
`bgt-land-cover-summary`. It currently executes synchronously and accepts the
original point/two-radius inputs.

The processor returns one named output internally. The local
`OgcSynchronousManager` is the HTTP-boundary adapter for the pinned pygeoapi
0.23.4 release: it returns the summary itself for a raw request and a
`summary`-keyed qualified-value map for a document request. It also removes the
framework's unconditional Callback declaration from the public synchronous
service. This is an explicit compatibility seam, not calculation logic. A
future PostgreSQL/asynchronous manager must preserve the same response contract
when results are retrieved. Its initial asynchronous execution response instead
uses `201` status information. It may declare Callback only after that product
lifecycle is tested.

## Staged capability activation

The pinned pygeoapi release contains generic async, job and subscriber code,
but its presence does not mean that the product process implements those
capabilities. The public contract is controlled by process metadata, the
configured manager, the WSGI request guard, the generated-OpenAPI correction
and product HTTP tests together. Change these layers as one reviewed feature;
never infer support merely from a pygeoapi route being available.

The current sync-only state is enforced deliberately:

- `PROCESS_METADATA.jobControlOptions` contains only `sync-execute`;
- `OgcSynchronousManager` ignores an async preference, rejects subscribers and
  removes pygeoapi's unconditional Callback conformance declaration;
- the WSGI request guard rejects every `subscriber` member;
- the OpenAPI correction removes the generated `201` response; and
- the product HTTP tests assert all four restrictions.

Persistent async may be activated before Callback. When async execution is
implemented, the PostgreSQL manager must reuse `format_process_result`, add
`async-execute` to the process description, restore an accurate `201` response,
and return `Location` and `Preference-Applied: respond-async` only after durable
job creation succeeds. The stored job result must use the same raw/document
contract as synchronous execution. Update the product HTTP tests and reviewed
Geonovum baseline in the same change.

Callback is a separate activation step. Keep subscriber rejection and the
Callback conformance URI absent until the durable callback queue, bounded
retries and timeouts, outcome recording, and outbound-URL safeguards have been
tested end to end. Enabling an async manager alone must not advertise Callback.

Job List is another explicit step: implement all filters required by the
selected checker profile, describe them in OpenAPI, add runtime tests, and only
then remove the corresponding baseline diagnostics. The outstanding work is
also tracked in [delivery requirements](delivery-requirements.md).

An integration-only configuration adds a predictable `async-echo` fixture and
TinyDB manager. The fixture gives OGC CITE a controlled process for testing
synchronous and asynchronous API execution without terrain-specific inputs or
live PDOK data. TinyDB state is disposable and does not demonstrate persistent
jobs or recovery after a restart. This setup is not part of the public API or
the target architecture.

## Target delivery architecture

```text
                    +----------------+
client ------------>| pygeoapi / API |
                    +-------+--------+
                            |
               +------------+-------------+
               |                          |
        synchronous core          bounded job queue
                                           |
                                           v
                                    worker processes
                                           |
                     +---------------------+------------------+
                     |                                        |
                 PDOK BGT                              callback delivery
                     |
                     v
              calculation core
                     |
                     v
           PostgreSQL job/result state
```

Synchronous requests and workers call the same calculation core. Persistent
job/result state is separate from disposable containers. Callback delivery
cannot block calculation workers. The exact queue/worker implementation is an
open architecture decision and must be recorded before implementation. The
current TinyDB integration can inform that work, but PostgreSQL is the planned
persistent store; reuse must be decided from behaviour and tests rather than
assuming that the temporary storage design carries over.

## Package boundary

Breinstein code lives in the installable `bkn_terrain_processes` package. It
must not be copied into or imported under pygeoapi's own `pygeoapi.process`
namespace. Pygeoapi supplies the standard HTTP framework; the calculation and
its contract remain independently testable. Version-specific compatibility is
implemented through pygeoapi's plugin boundary and the narrow generated
OpenAPI correction, rather than by maintaining a private copy of pygeoapi.
