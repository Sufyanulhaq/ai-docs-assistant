# Getting started with Fernhill

Fernhill is a workflow platform that runs your scheduled jobs and data pipelines in the cloud. This guide covers the first ten minutes.

## Create your account and workspace

Sign up at app.fernhill.example with a work email. You will be asked to name your workspace. The workspace is the container for your pipelines, runs, API keys and billing, so most teams use their company name.

Every new workspace starts on the Free plan. You can upgrade at any time from Settings, then Billing.

## Invite your team

Open Settings, then Members, and choose Invite. Enter one or more email addresses and pick a role for each person. Invitations expire after 7 days and can be resent.

## Roles

Fernhill has four roles:

- Owner: full control, including billing and deleting the workspace. Every workspace has at least one Owner.
- Admin: manages members, API keys and integrations, but cannot change billing or delete the workspace.
- Member: creates and edits pipelines and can start runs.
- Viewer: read only access to pipelines and run history.

## Build your first pipeline

Choose New pipeline, give it a name and pick a trigger: a schedule, a webhook or a manual start. Add steps in order, then press Run once to test it. Most people have a working pipeline in about five minutes.

Each execution of a pipeline is called a run. Runs are counted against your monthly run allowance, which depends on your plan.
