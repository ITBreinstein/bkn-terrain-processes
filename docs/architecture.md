# Architecture

## Current system

```text
client
  |
  v
pygeoapi 0.23.4 / Flask
  |
  +-- request guard and synchronous result adapter
  |
  v
BgtLandCoverSummaryProcessor
  |
  v
terrain calculation
  |
  v
PDOK BGT OGC API Features
```

The normal configuration exposes one process: `bgt-land-cover-summary`. It
accepts latitude, longitude and two radii, executes in the request thread and
returns a JSON summary. The calculation converts the centre to EPSG:28992 for
metric buffers and retrieves five BGT feature collections from PDOK.

PDOK pages are followed through their opaque `rel=next` links. All collection
requests use the same retrieval timestamp. Feature geometries are clipped to
the two circles, assigned to application-defined categories and de-duplicated
before their area percentages are calculated.

## pygeoapi compatibility boundary

Pygeoapi supplies discovery, routing, process descriptions and the base
execution machinery. Breinstein code remains in the installable
`bkn_terrain_processes` package rather than being copied into pygeoapi's own
namespace.

Three narrow adapters make the public contract explicit for the pinned
pygeoapi 0.23.4 release:

1. `app.py` rejects malformed execution documents and subscriber requests
   before framework internals can turn them into an HTML server error.
2. `manager.py` runs synchronously, converts the processor's internal named
   output to the OGC raw or document representation and removes the Callback
   conformance declaration that the service has not implemented.
3. `patch_pygeoapi_openapi.py` corrects known generated-document gaps after
   pygeoapi creates its OpenAPI file at container startup. It describes
   existing process-list limiting and 404 behaviour, documents the synchronous
   result forms and removes the unimplemented asynchronous `201` response.

These adapters are version-specific. They need review if pygeoapi is upgraded;
a generated OpenAPI document is not assumed to describe runtime behaviour
correctly merely because the framework produced it.

## Capability boundary

The terrain process deliberately declares only `sync-execute`.

- `Prefer: respond-async` does not create a job and no
  `Preference-Applied: respond-async` header is returned.
- Every `subscriber` member is rejected.
- No asynchronous `201` response is advertised for this process.
- There is no durable job/result store, job dismissal or restart recovery.

The calculation has an optional in-process progress hook. Nothing in the
normal HTTP service connects that hook to an OGC job resource or subscriber;
it must not be mistaken for public asynchronous support.

## Integration-only fixture

`compose.integration.yml` replaces the synchronous manager with pygeoapi's
disposable TinyDB manager and adds `async-echo` from `tests/fixtures`. This
controlled process exists only because OGC CITE needs a predictable execution
contract for several generic runtime tests.

The fixture demonstrates selected pygeoapi routes, not terrain-process
capabilities. Its job state is disposable, its results are unrelated to BGT,
and it must not be deployed as the public API.

## Development container

The Compose service builds on `geopython/pygeoapi:0.23.4`. Configuration and
Breinstein source are mounted read-only from the working tree. This makes local
iteration straightforward but means the image is not a self-contained release
artifact. An internet-facing deployment would need a separately reviewed
image and operational design.
