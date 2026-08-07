# Validation

Validation has three layers:

1. unit and schema tests for deterministic calculation and contract behaviour;
2. HTTP/container integration tests for the running service and job lifecycle;
3. OGC CITE/TEAM Engine and Geonovum checker runs against the deployed API.

The validator version, selected conformance classes, configuration, date and
complete output must be saved with release evidence. A global pygeoapi
conformance declaration is not proof that this process implements or has
tested a capability.

The acceptance baseline is OGC API Processes v1. The exact Geonovum v1 checker
invocation and optional classes, including Job List, must be confirmed with
Geonovum before the process contract is frozen.

Live PDOK execution demonstrates interoperability, but independently reviewed
reference cases provide repeatable calculation evidence. The public process
does not gain a hidden dummy-data mode for those tests.
