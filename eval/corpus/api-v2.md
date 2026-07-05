# Meridian API v2 (current)

API v2 is the current version and is recommended for all workspaces.

The base URL for API v2 is `https://api.meridian.io/v2`. Requests authenticate with either
an API key in the `Authorization: Bearer` header or an OAuth 2.0 access token. v2 does not
accept the `X-Api-Key` header used by v1.

In v2, a pipeline is created with `POST /v2/pipelines` and the request body uses the field
`display_name` for the pipeline name and `definition` for the pipeline definition. v2
returns the created pipeline id in the `pipeline_id` field.

v2 pagination is cursor based, using a `cursor` query parameter and a `next_cursor` field
in the response. The maximum page size in v2 is 500 items. v2 responses wrap results in a
top-level `items` array.

v2 timestamps are returned as ISO 8601 strings in UTC. v2 returns a `Retry-After` header
on rate limiting so clients can honor the exact wait. Error responses in v2 use a
structured `error` object with `code` and `message` fields.
