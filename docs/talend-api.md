# Talend API setup

This path reads operational metadata through Talend API endpoints using a bearer credential stored only in your local process environment. This independent project is not affiliated with, sponsored by, or endorsed by Qlik.

`talend-api` is the name of this repository's Python CLI. It is not Qlik's separate Talend CommandLine product.

## Access is not bundled

The free repository does not include, create, or grant:

- a Talend account, subscription, license, or trial;
- a personal access token (PAT) or service account token (SAT);
- a role, workspace membership, or endpoint entitlement;
- access to any tenant, environment, project, task, or execution.

Use only an account and resources you are authorized to inspect. A credential can be valid while a particular endpoint is still forbidden. Credential support can differ by API and account configuration; check current Qlik documentation to confirm whether the endpoint you need accepts a PAT, SAT, or another documented mechanism.

## Regional API host

Talend API is hosted at an account-specific regional URL shaped like:

```text
https://api.<region>.cloud.talend.com
```

Use the exact HTTPS API root documented for your account. The CLI validates the `api.<region>.cloud.talend.com` shape, default HTTPS port, and empty root path. It rejects HTTP, URL credentials, custom ports, paths, queries, fragments, and lookalike host suffixes.

The `<region>` text is a placeholder, not a value to copy literally. The examples below use an intentionally non-runnable uppercase placeholder:

```text
https://api.YOUR_REGION.cloud.talend.com
```

Consult Qlik's current [Talend application URL mapping](https://help.qlik.com/talend/en-US/installation-guide-windows/Cloud/talend-cloud-application-url) for the host assigned to your authorized account.

## Configure the local process

The CLI reads two environment variables:

| Variable | Purpose | Required shape |
| --- | --- | --- |
| `TALEND_BASE_URL` | Exact regional Talend API root | `https://api.<region>.cloud.talend.com`, with no path/query/fragment |
| `TALEND_TOKEN` | Bearer credential accepted by the selected endpoint | Non-empty, single-line secret |

The repository does not auto-load `.env` files. `.env.example` documents names only. Never commit a populated environment file.

macOS or Linux:

```bash
export TALEND_BASE_URL="https://api.YOUR_REGION.cloud.talend.com"
read -s TALEND_TOKEN
export TALEND_TOKEN
talend-api talend workspaces
```

PowerShell:

```powershell
$env:TALEND_BASE_URL = "https://api.YOUR_REGION.cloud.talend.com"
$secureToken = Read-Host "Talend API token" -AsSecureString
$env:TALEND_TOKEN = [System.Net.NetworkCredential]::new("", $secureToken).Password
talend-api talend workspaces
```

Replace `YOUR_REGION` with the exact lowercase regional API root for your own account. The placeholder fails validation as written, preventing it from being mistaken for a verified live endpoint. The token is deliberately unavailable as a CLI flag because command arguments may appear in process listings and shell history.

## Read-only commands

Inspect help from the exact revision you installed:

```bash
talend-api talend workspaces --help
talend-api talend tasks --help
talend-api talend runs --help
```

The supported read surface maps to these endpoint families:

| Command | GET endpoint | Typical selectors |
| --- | --- | --- |
| `talend workspaces` | `/orchestration/workspaces` | Optional exact environment name |
| `talend tasks` | `/orchestration/executables/tasks` | Workspace ID or artifact ID, bounded limit/offset |
| `talend runs` | `/processing/executables/tasks/executions` | Workspace ID, documented status, bounded day window and page |

For task and run reads, one invocation requests one bounded page. Use the installed command's `--help` for the enforced limits. The CLI does not silently walk an unbounded account inventory.

Every request sends the documented `talend-version: 2021-03` header. Review the official [Talend API versioning policy](https://talend.qlik.dev/api-versioning-policy/), [Orchestration API](https://talend.qlik.dev/apis/orchestration/2021-03/), [Processing API](https://talend.qlik.dev/apis/processing/2021-03/), and [API authentication guide](https://help.qlik.com/talend/en-US/api-user-guide/Cloud/authentication) before live use. Provider contracts can change independently of this repository.

## Request policy

- HTTP method is always GET.
- Authorization is sent as a Bearer header only to the validated host.
- Redirects are not followed and authorization is never forwarded to another host.
- Request count, response size, page, selector, and time budgets are finite.
- Requests are not automatically retried.
- Provider error bodies, credentials, and raw responses are not copied into share-safe errors.
- Authentication, authorization, missing resource, rate limit, redirect, invalid JSON, and network failures use redacted categories.

The local view can contain operational names or IDs already visible to the caller. Do not publish it. Review even the identity-free share-safe output before sharing because aggregate statuses and counts can reveal architecture.

## What automated verification proves

The repository's default tests and examples use synthetic fixtures and mocked HTTP transports. They can verify request construction, host/endpoint policy, response parsing, error redaction, and output behavior without a real secret.

They do **not** prove that:

- a live tenant accepted authentication;
- your subscription or trial includes a specific endpoint;
- the selected PAT or SAT is supported by that endpoint;
- your role can see a workspace, task, or run;
- Studio `.item` source or business rows can be downloaded from these operational endpoints.

Confirm live access only in an account you control and are authorized to use. Do not submit a real credential, provider response, identifier, screenshot, or client artifact as test evidence.

## Remove credentials from the shell

macOS or Linux:

```bash
unset TALEND_TOKEN TALEND_BASE_URL
```

PowerShell:

```powershell
Remove-Item Env:TALEND_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:TALEND_BASE_URL -ErrorAction SilentlyContinue
```

Unsetting an environment variable does not revoke a credential. If exposure is possible, revoke or rotate it through the authorized provider interface immediately.

## Troubleshoot without leaking data

A public issue may contain the package version, operating system, command name, synthetic reproduction, and redacted error category. Never post a PAT, SAT, authorization header, provider response body, environment dump, tenant/workspace/task/run ID, client name, real regional host, live screenshot, or shell transcript containing environment values. See [Troubleshooting](troubleshooting.md).
