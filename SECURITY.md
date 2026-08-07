# Security policy

Do not report suspected vulnerabilities in a public issue. Contact the
Breinstein delivery team through the private contact channel agreed with the
project owner.

The current development baseline is not a production service. Before public
deployment, referenced-input and callback URLs must be protected against SSRF,
timeouts and excessive responses; secrets must be injected at runtime; and
dependency and container findings must be reviewed.
