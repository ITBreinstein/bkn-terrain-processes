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
its contract remain independently testable.
