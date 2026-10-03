# API keys and authentication

The Fernhill API lets you manage pipelines and runs from your own code. The base URL is https://api.fernhill.example/v2.

## Create an API key

Owners and Admins can create keys. Go to Settings, then Developer, then API keys, and choose Create key. Give it a name and choose its scopes.

The full key is shown only once, right after you create it, so copy it straight away into a secrets manager. If you lose it, create a new key.

Keys start with a prefix that tells you which environment they belong to: fh_live_ for production and fh_test_ for the sandbox. A fh_test_ key will not work against production data.

## Scopes

Each key only gets the scopes you choose:

- pipelines:read and pipelines:write
- runs:read and runs:write
- admin, which also allows managing members and other keys

Give a key the smallest set of scopes it needs.

## Sending the key

Send the key as a bearer token in the Authorization header:

Authorization: Bearer fh_live_xxxxxxxx

## Rotating keys

To rotate a key without downtime: create a new key with the same scopes, deploy it to your application, check that it works, then revoke the old key from the API keys page. Keys expire after 365 days by default. You can choose a shorter expiry when you create one.

## Rate limits

Limits apply per workspace, per minute: 60 requests on Free, 600 on Pro and 3,000 on Business. Every response includes an X-RateLimit-Remaining header. When you go over, the API returns status 429 with a Retry-After header telling you how many seconds to wait.
