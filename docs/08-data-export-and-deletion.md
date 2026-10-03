# Data export and deletion

## Export your data

Owners and Admins can export run history as CSV or JSON. Go to Settings, then Data, then Export, choose a date range and a format, and start the export.

- Exports can contain up to 1 million rows.
- When the file is ready we email a download link to you. The link works for 7 days.
- For automated exports, call POST /v2/exports with a key that has the runs:read scope. Large date ranges are much faster through the API than through the web page.

## Delete a workspace

Only an Owner can delete a workspace. Go to Settings, then General, then Delete workspace.

Deletion is not instant. The workspace is hidden straight away and kept for a 30 day grace period, during which an Owner can restore it from the same page. After the grace period the data is permanently deleted, and it disappears from backups within a further 90 days.

If you have an active paid plan, cancel it first so you are not charged again. Deleting a workspace does not refund payments.

## Delete your personal account

You can delete your own account from your profile page. If you are the only Owner of a workspace you must hand ownership to someone else, or delete the workspace, first.

## Privacy requests

To ask for a copy of your personal data or to have it removed under privacy law, email privacy@fernhill.example. We reply within 30 days.
