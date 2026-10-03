# Troubleshooting

## API errors

### 401 Unauthorized

The key is missing, mistyped or revoked, or it belongs to the wrong environment. A fh_test_ key does not work against production and a fh_live_ key does not work in the sandbox. Check the Authorization header, and check on the API keys page that the key has not expired or been revoked.

### 403 Forbidden

The key is valid but does not have the scope this request needs, for example writing a pipeline with a key that only has pipelines:read. Create a new key with the right scope. Existing keys cannot be edited.

### 404 Not found

The pipeline or run id does not exist in the workspace that owns your key. Ids from another workspace return 404.

### 429 Too Many Requests

You went over the per minute limit for your plan. Wait for the number of seconds in the Retry-After header, then try again, and spread your calls out rather than sending them in bursts.

## Webhooks that do not arrive

1. Make sure the endpoint is HTTPS and is reachable from the internet.
2. Check that it answers with a 2xx status in under 10 seconds.
3. Check that the event type is ticked on the endpoint.
4. If signature checks fail, use the raw request body and the signing secret of that specific endpoint.

The delivery log on the endpoint page shows the status code and response for each attempt.

## Pipelines stuck in Queued

A run waits in the queue when you have reached the concurrent run limit of your plan, which is 2 on Free, 10 on Pro and 50 on Business. A Free workspace also queues runs after its 1,000 monthly runs are used. Wait for running jobs to finish or upgrade the plan.

## File imports fail

CSV imports are limited to 50 MB per file. Split larger files, and check that the first row contains column names.

## Exports are slow or time out

Large date ranges take a long time on the web page. Use the export API with smaller date ranges, or export one month at a time.
