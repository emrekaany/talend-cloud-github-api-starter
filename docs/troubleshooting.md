# Troubleshooting

Start with the offline demo. It separates package/parser problems from local-path permissions, provider credentials, endpoint entitlements, network policy, repository visibility, and rate limits.

```bash
talend-api demo
```

Do not enable verbose HTTP logging with a live credential unless you have independently verified that authorization headers and response bodies are redacted.

## Installation

### `talend-api: command not found`

Confirm the virtual environment is active and test the module from the same Python environment:

```bash
python -m talend_api_starter --help
python -m pip list
```

If the module form works, reactivate `.venv` or invoke the executable from the environment's `bin` / `Scripts` directory.

### Python version error

```bash
python --version
```

Use Python 3.10 or newer. Create a new virtual environment with the intended interpreter rather than replacing the system Python.

## Offline demo

### Demo requests a token or contacts a provider

Stop. That violates the demo contract. Record only the installed revision, command, operating system, and a sanitized description. If data may have left the machine, use the private vulnerability route in [SECURITY.md](../SECURITY.md). Do not attach packet captures or logs containing local details to a public issue.

### Demo reports unsupported XML

Bundled fixtures should remain supported. Reinstall from a clean copy of the same revision and rerun. If it persists, open a bug using the bundled fixture's command and redacted error category; do not attach any real Talend file.

## Local project

### Project path not found or not a directory

Pass an existing directory you are authorized to read:

```bash
talend-api local jobs /path/to/TALEND_PROJECT --path-prefix process
```

Do not paste an actual private path into an issue. Reproduce the behavior in a temporary synthetic directory.

### Path prefix rejected

The prefix is relative to the selected project root. Use a normalized path such as `process`; do not use an absolute path, `..`, control characters, or an escape through a symlink or other indirection.

### No supported jobs found

Confirm that the selected prefix contains Talend Studio process descriptors and matching `.item` artifacts in a supported shape. The CLI does not infer a pair from similar filenames alone. Use a newly authored synthetic pair to test the parser without exposing a real project.

### Local budget exceeded

Choose a narrower project root or prefix. Budgets protect against accidental broad scans; do not bypass them by moving private artifacts into public fixtures.

## Talend API

### Missing configuration

Set `TALEND_BASE_URL` and `TALEND_TOKEN` in the same shell that runs `talend-api talend ...`. The project does not load `.env` automatically.

Never print the token to test it. Check only whether the variable is set using a shell method that does not echo its value.

### Base URL rejected

Use the exact regional API root assigned to your account. It must match:

```text
https://api.<region>.cloud.talend.com
```

Remove paths, queries, fragments, URL credentials, custom ports, and trailing provider endpoints. Do not post a real tenant-specific configuration or shell transcript publicly.

### `authentication_failed` / HTTP 401

- Confirm the credential has not expired or been revoked.
- Confirm the token value has no surrounding newline.
- Confirm the regional host belongs to the authorized account.
- Check current Qlik documentation to verify whether the endpoint accepts your PAT, SAT, or other configured credential type.
- Rotate the credential immediately if exposure is possible.

Automated mock-transport tests cannot prove that a live tenant accepts your credential.

### `forbidden` / HTTP 403

Authentication may have succeeded while the account lacks a role, workspace membership, subscription feature, or endpoint entitlement. Use the approved private route to your Talend administrator or Qlik support. Trying unrelated credentials is not automatically a valid fix.

### `not_found` / HTTP 404

The resource may not exist in the selected region, may be outside account scope, or may be hidden by permissions. Verify region and selectors locally. Do not post identifiers publicly.

### `rate_limited` / HTTP 403 or 429

Respect provider reset or `Retry-After` guidance. Reduce repeated calls and page size. The CLI does not bypass provider limits.

## Public GitHub

### Repository or ref not found

Confirm that the repository is public and the owner, repository, and ref are spelled correctly. Private repository authentication is outside scope; never post a private URL as an example.

### Path prefix not found

The path is repository-relative and case-sensitive. It must identify a directory and use normalized `/` separators.

### Budget exceeded or incomplete tree

Choose a narrower project/process path. Safety ceilings are part of the command contract. Do not work around them by downloading and posting client artifacts.

### Unsupported pair or format

Talend versions and repository histories can encode relationships differently. Build the smallest **newly authored synthetic** reproduction you can legally publish. Never attach a real `.item` or `.properties` file, even if you believe it contains no secret.

## What a public issue may contain

- installed version or commit SHA;
- operating system and Python version;
- command name and mode, without real paths or identifiers;
- redacted error category;
- steps using bundled or newly created synthetic fixtures;
- expected versus actual behavior.

It must not contain credentials, headers, environment dumps, client/employer names, live IDs, real regional hosts, private URLs, provider response bodies, raw source, outputs, screenshots, logs, or files derived from a real project.

Use [SUPPORT.md](../SUPPORT.md) for public support scope and [SECURITY.md](../SECURITY.md) for the private vulnerability route.
