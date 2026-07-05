# Meridian Platform — Authentication

Meridian supports two authentication methods: API keys and OAuth 2.0.

API keys are created in the workspace settings. A production API key is prefixed with
`mk_live_` and a staging key is prefixed with `mk_test_`. A production API key does not
expire until it is revoked. A staging API key expires 30 days after it is created.

OAuth access tokens are short lived. A production access token is valid for 60 minutes and
a staging access token is valid for 15 minutes. Refresh tokens are valid for 30 days on
both environments and are rotated on every use.

Failed authentication is rate limited: after five failed attempts from one IP address
within one minute, that IP is blocked for 15 minutes. Successful authentication resets the
counter.

Service accounts are available on Team and Enterprise plans. A service account
authenticates with a key pair and is scoped to a single pipeline by default. Scopes can be
widened in the service-account settings but never span workspaces.
