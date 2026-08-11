# Talend Cloud API setup

This path reads operational metadata from Qlik Talend Cloud® using a personal access token stored only in your local process environment. This independent project is not affiliated with, sponsored by, or endorsed by Qlik.

## What you supply

The repository does not include or grant:

- a Talend Cloud account, license, or trial;
- a personal access token (PAT);
- a role, workspace membership, or endpoint entitlement;
- access to any tenant, environment, project, task, or execution.

Use only an account and resources you are authorized to inspect. A token can be valid while a particular endpoint is still forbidden.

## Configure the local process

The CLI reads exactly two environment variables:

| Variable | Purpose | Allowed values |
| --- | --- | --- |
| `TALEND_BASE_URL` | Exact API root for your Talend Cloud region | `https://api.<region>.cloud.talend.com` with no path/query/fragment |
| `TALEND_TOKEN` | Bearer personal access token | Non-empty single-line secret |

macOS or Linux:

```bash
export TALEND_BASE_URL="https://api.eu.cloud.talend.com"
read -s TALEND_TOKEN
export TALEND_TOKEN
talend-api-starter cloud workspaces
```

PowerShell:

```powershell
$env:TALEND_BASE_URL = "https://api.eu.cloud.talend.com"
$securePat = Read-Host "Talend Cloud PAT" -AsSecureString
$env:TALEND_TOKEN = [System.Net.NetworkCredential]::new("", $securePat).Password
talend-api-starter cloud workspaces
```

The repository does not auto-load `.env` files. `.env.example` documents variable names only. Do not commit a populated copy.

The example uses the EU host only as a format illustration. Use the exact API host documented for your account in Qlik's [Talend Cloud application URL mapping](https://help.qlik.com/talend/en-US/installation-guide-windows/Cloud/talend-cloud-application-url); the application does not impose a closed list of region labels. It validates HTTPS, the `api.<region>.cloud.talend.com` host pattern, the default port, and an empty root path.

The token is deliberately unavailable as a CLI flag: command arguments can appear in process listings and shell history.

## Commands

Start with help from the exact revision you installed:

```bash
talend-api-starter cloud workspaces --help
talend-api-starter cloud tasks --help
talend-api-starter cloud runs --help
```

The supported read surface maps to these endpoint families:

| Command | GET endpoint | Typical selectors |
| --- | --- | --- |
| `cloud workspaces` | `/orchestration/workspaces` | Optional exact environment name |
| `cloud tasks` | `/orchestration/executables/tasks` | Workspace ID or artifact ID, bounded limit/offset |
| `cloud runs` | `/processing/executables/tasks/executions` | Workspace ID, documented run status, 1–10 day window, bounded limit/offset |

For tasks and runs, one CLI invocation requests exactly one bounded page: limit 1–100 and offset 0–1,000. The starter does **not** paginate automatically; request a later offset explicitly when authorized and needed. The runs window is limited to 1–10 days and defaults to seven. Workspaces use the provider's documented raw-array response rather than the paged task/run shape. These are local safety limits, not statements about provider capacity.

Every Talend request sends `talend-version: 2021-03` in line with the official [Talend API versioning policy](https://talend.qlik.dev/api-versioning-policy/). The provider references are the official [Talend Cloud Orchestration API](https://talend.qlik.dev/apis/orchestration/2021-03/) and [Processing API](https://talend.qlik.dev/apis/processing/2021-03/). Authentication requirements and supported credential types should be checked against the current [Talend Cloud API authentication guide](https://help.qlik.com/talend/en-US/api-user-guide/Cloud/authentication).

## Host policy

`TALEND_BASE_URL` must be an exact root URL matching this shape:

```text
https://api.<region>.cloud.talend.com
```

The `<region>` label is validated rather than selected from a hard-coded closed enum, so newly documented regional hosts can work without weakening the host boundary. Custom ports, URL credentials, paths, queries, fragments, lookalike suffixes, and HTTP are rejected. Redirects are not followed. Provider response fields cannot supply a new URL for the client to call.

## Request and response policy

- HTTP method is always GET.
- Authorization is sent as a Bearer header only to the validated host.
- Default request count and response-byte budgets stop unbounded reads.
- Connect/read/write/pool timeouts are finite.
- Requests are not automatically retried; after a redacted error, the caller decides whether a new attempt is appropriate.
- HTTP error bodies are not copied into the safe error object.
- 401, 403, 404, 429, redirects, invalid JSON, and network errors receive redacted categories.

The CLI may show metadata that your own account is authorized to read in a local view. Before sharing anything, use only the documented share-safe output and still review it manually.

## What live mode does not prove

Successful authentication does not prove that:

- every listed endpoint is enabled for your subscription or trial;
- service-account credentials work on PAT-only endpoints;
- a resource outside your role should be visible;
- Studio `.item` source can be downloaded through the Cloud API;
- job business data can be read through these metadata endpoints.

This starter makes none of those claims.

## Remove the token from the shell

macOS or Linux:

```bash
unset TALEND_TOKEN TALEND_BASE_URL
```

PowerShell:

```powershell
Remove-Item Env:TALEND_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:TALEND_BASE_URL -ErrorAction SilentlyContinue
```

If a token may have been exposed, revoke it in the provider UI. Unsetting an environment variable does not revoke a credential.

## Troubleshooting without leaking data

Share only the package version, operating system, command name, non-sensitive region label, and redacted error category. Never post a PAT, authorization header, provider response body, tenant/workspace/task/run ID, client name, screenshot of a live tenant, or shell transcript containing environment values. See [Troubleshooting](troubleshooting.md).
