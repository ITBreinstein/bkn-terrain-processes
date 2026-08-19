# Topic 1 delivery requirements

This document translates the awarded plan of approach into implementation and
acceptance work. It contains no commercial, partner or tender-evaluation
material. A checked item requires saved evidence; source code alone is not
automatically acceptance evidence.

## Process contract

- [x] Stable process identifier: `bgt-land-cover-summary`.
- [ ] Publish versioned JSON Schemas, examples, units, CRS, limits and error
      responses matching live behaviour and OpenAPI.
- [ ] Reject input components that do not satisfy those schemas; do not coerce
      numeric strings or truncate decimal values for integer fields.
- [ ] Accept RFC 7946 GeoJSON Point, Polygon and MultiPolygon through
      `analysis_geometry`, in CRS84 longitude-latitude order.
- [ ] Also accept a raw Point through separate numeric `latitude` and
      `longitude` inputs as a documented convenience form; require exactly one
      of this pair or `analysis_geometry` in each request.
- [ ] Require `outer_radius_m` for a GeoJSON Point or raw coordinate pair and
      prohibit it for Polygon and MultiPolygon.
- [ ] Allow `inner_radius_m` for a GeoJSON Point or raw coordinate pair, not
      greater than `outer_radius_m`; prohibit it for Polygon and MultiPolygon.
- [ ] Support the optional published `method_version` value.
- [ ] Accept geometry inline and by HTTPS reference with bounded download,
      redirect and timeout behaviour and protection against private/internal
      destinations.
- [ ] Transform valid geometries to RD New (EPSG:28992) for metric operations.
- [ ] Enforce published radius, area, bounding-box, part, vertex and download
      limits.
- [ ] Reject malformed coordinate nesting, unsupported geometry types or CRS
      declarations, non-finite/out-of-range coordinates, empty and zero-area
      geometry, invalid rings/holes, self-intersections, and overlapping
      Polygon/MultiPolygon components with documented machine-readable errors.
- [ ] Distinguish structurally valid geometry outside the supported Dutch
      service area from malformed geometry and from unavailable PDOK coverage.

## Results and source behaviour

- [x] Return BKN-oriented vegetation, water, road, built, explicitly unpaved
      and unknown-classification percentages for the current point baseline.
- [ ] Return one consistently structured summary for a point with one radius
      or for Polygon/MultiPolygon, and two summaries for a point with an inner
      radius.
- [ ] Include method version, source collections, feature counts, retrieval
      time and execution timings.
- [ ] Report no matching BGT objects as an out-of-coverage error, not as valid
      zero percentages.
- [ ] Represent partial geographic or collection coverage with an explicit
      unavailable-area category and warning.
- [ ] Report an unavailable PDOK service as an upstream error or failed job,
      not as a valid calculation.
- [ ] Keep the BKN proxy limitations visible in metadata and documentation.

## Execution and job management

- [x] The current point calculation can be invoked synchronously. This checks
      the calculation path and the current inline coordinate/radius HTTP
      contract; GeoJSON and referenced inputs remain outstanding Core work.
- [x] Return the single `summary` value itself for default/raw synchronous
      execution and the OGC 1.0 results map for document execution.
- [ ] Keep process metadata, `/conformance`, OpenAPI status/response schemas and
      running behaviour consistent; do not advertise async or Callback before
      those capabilities work end to end.
- [ ] Measure and publish the synchronous runtime/complexity threshold.
- [ ] Instruct clients above that threshold to resubmit with
      `Prefer: respond-async`.
- [ ] Return `201 Created`, `Location` and
      `Preference-Applied: respond-async` for accepted asynchronous work.
- [ ] Execute synchronous and asynchronous requests through the same
      calculation core.
- [ ] Execute jobs in a separate, concurrency-bounded worker context.
- [ ] Persist job state and results in PostgreSQL across service restarts.
- [ ] Mark work interrupted by restart as failed with an explanatory message.
- [ ] Expose standard status vocabulary, progress and messages where
      available.
- [ ] Support Dismiss through `DELETE /jobs/{jobId}` for running and completed
      jobs.
- [ ] Retain completed results for 14 days and clean them automatically.
- [ ] Implement Job List and the filters required by the selected Geonovum
      checker profile as part of the final job-management delivery.

## Callbacks and security

- [ ] Use the execution request's `subscriber` object with `successUri`,
      `inProgressUri` and `failedUri`.
- [ ] Deliver callbacks outside calculation workers with bounded retries,
      connection/read timeouts and recorded outcomes.
- [ ] Reject loopback, link-local, private and internal-service callback and
      referenced-input destinations, including unsafe redirect targets.
- [ ] Test DNS resolution/rebinding controls, unreachable subscribers,
      timeouts and retry exhaustion.

## Verification and evidence

- [ ] Publish at least two point reference cases and one small polygon case.
- [ ] Store the source features, retrieval date, licence, attribution,
      ready-to-run requests and expected results with the reference package.
- [ ] Calculate expected areas and percentages independently through a
      documented desktop-GIS workflow and review them before committing.
- [ ] Test classification, buffers, polygons, clipping, overlaps, unknowns,
      complete response schemas and advertised limits.
- [ ] Test bow-tie/self-intersecting and self-touching rings, holes outside or
      crossing their shell, overlapping holes, overlapping MultiPolygon
      members, zero-area and empty geometry, malformed coordinate nesting,
      invalid coordinates, unsupported types/CRS declarations, excessive
      area/bounds/parts/vertices and oversized references.
- [ ] Run formatting, linting, security checks and unit tests on pull requests
      and `main`.
- [ ] Exercise `bgt-land-cover-summary` through HTTP and verify exact input
      validation, statuses, headers, raw/document bodies and error documents.
- [ ] Save zero-error evidence from the agreed OGC CITE/TEAM Engine v1 suite,
      recording that its controlled echo execution is generic server evidence.
- [ ] Save zero-error evidence from the agreed Geonovum v1 checker profile,
      recording which declared and optional conformance classes it applies.
- [ ] Test discovery, schemas, sync, async, jobs, results and callbacks with
      independent clients at both plugfests.

## Delivery and operation

- [ ] Maintain the implementation-findings report in Markdown for Geonovum.
- [ ] Publish versioned releases, schemas, examples, validation instructions
      and how-to documentation.
- [ ] Operate the delivered API as a public demo with monitoring, backups and
      a named operational owner.
- [ ] Keep the service and delivery material available for at least six months
      after testbed completion.
- [ ] Publish short videos covering discovery, sync execution, async jobs,
      results and callbacks.
