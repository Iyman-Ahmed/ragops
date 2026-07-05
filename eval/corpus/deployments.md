# Meridian Platform — Deployments & Rollbacks

Meridian supports blue-green deployments. A new revision is started alongside the current
one and traffic is shifted only after health checks pass.

To deploy a pipeline, run `meridian deploy --pipeline <name>`. The command builds the
image, uploads it, and starts a new revision. Deployments are zero-downtime by default.

An automatic rollback is triggered when the readiness health check fails three times in a
row within 90 seconds. On rollback, traffic returns to the last revision that passed all
health checks. Rollbacks are recorded in the audit log on Enterprise workspaces.

To roll back manually, run `meridian rollback --to <revision>`. To list revisions, run
`meridian revisions list`. Each revision is retained for 30 days before garbage
collection.

Deployment concurrency follows the plan: Starter allows one in-flight deployment, Team
allows five, and Enterprise is unlimited. A deployment that exceeds the plan limit is
queued rather than rejected.
