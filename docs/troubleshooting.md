# Troubleshooting

Start with a safe question: does the offline demo work? It separates installation/parser problems from provider credentials, permissions, network policy, repository visibility, and rate limits.

Use an output directory owned and controlled by your current user. Symlink/junction destinations and unsafe writable directories are rejected; on Windows, final access control still depends on the filesystem DACL.

```bash
talend-api-starter demo
```

Do not enable verbose HTTP logging with a live token unless you have verified that authorization headers and response bodies are redacted.

## Installation

### `talend-api-starter: command not found`

Confirm that the virtual environment is active and the package is installed into the same Python environment:

```bash
python -m pip show talend-cloud-github-api-starter
python -m talend_api_starter --help
```

If the module form works, reactivate `.venv` or invoke the console script from the environment's `bin` / `Scripts` directory.

### Python version error

```bash
python --version
```

Use Python 3.10 or newer. Create a new virtual environment with the intended interpreter rather than replacing the system Python.

## Offline demo

### Demo requests a token or contacts a provider

Stop. That violates the demo contract. Record only the package version, command, operating system, and a sanitized description; then report it through the security route if data may have left the machine. Do not attach packet captures or logs containing local details to a public issue.

### Demo reports unsupported XML

Bundled fixtures should remain supported. Reinstall from a clean checkout of the same revision and rerun. If it persists, open a bug with the commit SHA and error category; the repository already contains the synthetic fixture, so do not attach any real Talend file.

## Talend Cloud

### Missing configuration

Set `TALEND_BASE_URL` and `TALEND_TOKEN` in the same shell that runs the command. The project does not load `.env` automatically.

```bash
printf '%s\n' "$TALEND_BASE_URL"
```

Never print the token to test it. If you are unsure whether it is set, check only whether the variable is empty using a shell-safe method that does not echo the value.

### `authentication_failed` / HTTP 401

- Confirm the PAT has not expired or been revoked.
- Confirm there are no newline characters around the token.
- Confirm the selected region belongs to the account.
- Recreate the token if exposure is possible.

Do not paste the token or provider error body into an issue.

### `forbidden` / HTTP 403

Authentication may have succeeded while the account lacks the role, workspace membership, subscription feature, or endpoint entitlement. Ask your authorized Talend administrator or Qlik support using their approved private channel. A different token is not automatically the correct fix.

### `not_found` / HTTP 404

The resource may not exist in the selected region, may be outside your account scope, or may be hidden by permissions. Verify the region and selectors locally. Do not post IDs publicly.

### `rate_limited` / HTTP 403 or 429

Respect the provider's reset or `Retry-After` guidance. Reduce repeated calls and page size. The starter does not bypass provider limits.

## Public GitHub

### Repository or ref not found

Confirm the repository is public and the owner, repository, and ref are spelled correctly. Private repository URLs are outside scope and should never be posted as examples.

### Path prefix not found

The path is repository-relative and case-sensitive. It must identify a directory, not a file, and must not start or end with `/`.

### Budget exceeded

Choose a narrower project/process path. Safety budgets are part of the product contract; do not work around them by downloading and posting client artifacts.

### Unsupported pair or format

Talend project versions and histories can encode relationships differently. Build the smallest **synthetic** reproduction you can legally publish. Never attach a real `.item` or `.properties` file, even if you believe it contains no secret.

## What a public bug report may contain

- package version or commit SHA;
- operating system and Python version;
- command name and mode, without live identifiers;
- redacted error category;
- steps using only bundled or newly created synthetic fixtures;
- expected versus actual behavior.

It must not contain tokens, headers, environment dumps, client/employer names, live tenant/resource IDs, private URLs, provider response bodies, raw source, screenshots, logs, or files derived from a real project.

Use [SUPPORT.md](../SUPPORT.md) to choose the right channel and [SECURITY.md](../SECURITY.md) for vulnerabilities.
