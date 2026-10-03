# Webhooks

Webhooks let Fernhill call your server when something happens, so you do not need to poll the API.

## Add an endpoint

Go to Settings, then Developer, then Webhooks, and choose Add endpoint. Enter an HTTPS URL and tick the events you want. Each endpoint gets its own signing secret, which starts with whsec_.

## Events

- run.started
- run.succeeded
- run.failed
- pipeline.updated
- invoice.payment_failed

Use the Send test event button on the endpoint page to try your handler without waiting for a real run.

## Your endpoint must answer quickly

Your server has to reply with a 2xx status within 10 seconds. Do the slow work after replying, for example by putting the event in a queue. Any other status, or a timeout, counts as a failed delivery.

## Retries

Failed deliveries are retried up to 8 times with exponential backoff, spread over 24 hours. After the last attempt the event is marked as failed, and you can resend it by hand from the endpoint page. Because of retries, the same event can arrive more than once. Every event has a unique id, so store the ids you have handled and ignore repeats.

## Verify the signature

Every request carries a Fernhill-Signature header that looks like t=1700000000,v1=abcdef. To check it:

1. Take the timestamp t and the raw request body, and join them as t, a dot, then the body.
2. Compute an HMAC with SHA 256 using your endpoint signing secret.
3. Compare the result with v1 using a constant time comparison.
4. Reject the request if t is more than 5 minutes old.

Always use the raw body. If your framework parses the JSON first and you then rebuild the body from it, the signature will not match.
