# Meridian Platform — Observability

Every pipeline emits metrics, logs, and traces that are retained according to the plan.

Metrics are scraped every 15 seconds and retained for 15 days on Starter, 30 days on Team,
and 90 days on Enterprise. The built-in dashboard shows throughput, error rate, and
end-to-end latency per pipeline.

Structured logs are emitted as JSON. Logs are retained for 3 days on Starter, 14 days on
Team, and 30 days on Enterprise. Logs can be forwarded to an external sink such as
Datadog or an S3 bucket on Team and Enterprise plans.

Alerts are configured per pipeline. A default alert fires when the error rate exceeds 5
percent over a 5-minute window. A second default alert fires when end-to-end latency at
the 95th percentile exceeds 2 seconds. Alerts can be delivered to email, Slack, or a
webhook.

Distributed tracing is sampled at 10 percent by default. The sampling rate can be raised
to 100 percent for a single pipeline while debugging, which is not recommended in
production because it increases storage cost.
