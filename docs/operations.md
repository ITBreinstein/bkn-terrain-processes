# Operations

The named operational owner and hosting environment are confirmed outside the
source repository. Operational evidence must cover:

- availability and error monitoring;
- PDOK upstream failures and latency;
- queue depth, worker failures and stuck jobs;
- callback attempts and terminal failures without logging secrets;
- 14-day result cleanup;
- database backup and restore checks;
- dependency and container updates; and
- at least six months of public service after testbed completion.
