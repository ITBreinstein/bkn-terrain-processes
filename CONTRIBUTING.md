# Contributing

Create changes on a short-lived branch and open a pull request against `main`.
Pull requests should explain the behaviour affected, the checks performed and
any limitation that remains.

Use focused titles such as:

- `feat: support a new process input`
- `fix: reject incomplete PDOK responses`
- `test: cover synchronous document responses`
- `docs: clarify validation evidence`

All automated checks must pass. Add or update tests with behavioural changes.
Changes to the public process schema, classification method, validation
baseline or deployment architecture need an explicit review because they can
change what users may reasonably infer from the API.

See [Development workflow](docs/development.md) for local setup and checks.
