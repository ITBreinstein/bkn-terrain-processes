# Security policy

Do not report a suspected vulnerability in a public issue. Use GitHub's
**Security** tab and private vulnerability-reporting option when it is
available for this repository. Otherwise, contact Breinstein through the
[company contact page](https://www.breinstein.nl/contact-opdrachtgevers/) and
ask for a private channel for the open-source maintainers.

Include the affected version or commit, a concise reproduction and the likely
impact. Do not include secrets or personal data.

This repository provides a self-contained prototype image, not a managed
production service. The release Compose configuration runs as a non-root user,
uses a read-only root filesystem, drops Linux capabilities and prevents
privilege escalation. Its public process accepts numeric values and makes
outbound requests only to configured PDOK collection URLs. The integration-only
configuration and TinyDB job manager are test fixtures and must not be exposed
as a public service.

Before any internet-facing deployment, the image and dependencies, resource
limits, network policy, logging, secrets, update policy and operational
ownership require a separate security review.
