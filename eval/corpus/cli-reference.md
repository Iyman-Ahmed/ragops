# Meridian Platform — CLI Reference

The Meridian CLI is installed with `pip install meridian-cli`. Authenticate once with
`meridian login`, which stores a token in `~/.meridian/credentials`.

Common commands:

- `meridian deploy --pipeline <name>` builds and deploys a pipeline revision.
- `meridian rollback --to <revision>` restores a previous revision.
- `meridian logs -f --pipeline <name>` streams logs, following new lines.
- `meridian status` prints the health of every pipeline in the workspace.
- `meridian secrets set KEY=VALUE` stores an encrypted pipeline secret.
- `meridian run --pipeline <name> --once` triggers a single ad-hoc run.

The CLI reads configuration from `meridian.yaml` in the project root. A `--workspace` flag
overrides the default workspace for any command. A `--json` flag makes any command emit
machine-readable output for scripting.

The CLI version must be within one minor version of the platform API. Run `meridian
version` to print both the client and server versions. If they are incompatible the CLI
refuses to deploy and prints an upgrade instruction.
