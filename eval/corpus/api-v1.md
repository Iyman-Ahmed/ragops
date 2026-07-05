# Meridian API v1 (deprecated)

API v1 is deprecated and will be removed on 2026-12-31. New workspaces should use v2.

The base URL for API v1 is `https://api.meridian.io/v1`. Requests authenticate with an API
key passed in the `X-Api-Key` header. v1 does not support OAuth.

In v1, a pipeline is created with `POST /v1/pipelines` and the request body uses the field
`name` for the pipeline name and `spec` for the pipeline definition. v1 returns the created
pipeline id in the `id` field.

v1 pagination uses `offset` and `limit` query parameters. The maximum page size in v1 is
100 items. v1 responses wrap results in a top-level `data` array with no cursor.

v1 timestamps are returned as Unix epoch seconds. v1 does not return a `Retry-After`
header on rate limiting; clients must back off with a fixed 30-second delay. Error
responses in v1 use an `error_code` string field.
