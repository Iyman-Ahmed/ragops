# Meridian Platform — Rate Limits

The Meridian API enforces per-plan request limits, measured per workspace.

Starter workspaces are limited to 60 API requests per minute. Team workspaces are limited
to 600 API requests per minute. Enterprise workspaces are limited to 6000 API requests per
minute. Bursts of up to twice the limit are allowed for 10 seconds before requests are
throttled.

When a workspace exceeds its limit, the API responds with HTTP 429 and a `Retry-After`
header indicating how many seconds to wait. Throttled requests are not billed.

Pipeline execution has a separate limit. A single pipeline may process at most 1000 events
per second on Starter, 10000 events per second on Team, and 100000 events per second on
Enterprise. Events beyond the limit are buffered for up to 5 minutes and then dropped.

Webhook delivery is retried with exponential backoff for up to 24 hours. After 24 hours a
webhook is marked failed and moved to the dead-letter queue.
