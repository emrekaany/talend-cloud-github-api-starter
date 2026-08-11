# Quickstart

Run the complete offline path first. It proves that the package, command, synthetic cloud/Studio fixtures, parser, and sanitizer work without asking for a Talend account or a GitHub token.

## Before you start

You need:

- Python 3.10 or newer;
- Git, or a downloaded copy of the repository;
- a terminal on macOS, Linux, or Windows.

The editable install may download Python dependencies. Once installed, `demo` uses bundled synthetic cloud responses and `.item` / `.properties` inputs and makes no Talend Cloud or GitHub API calls.

## macOS or Linux

```bash
cd talend-cloud-github-api-starter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
talend-api-starter demo
```

## Windows PowerShell

```powershell
Set-Location talend-cloud-github-api-starter
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
talend-api-starter demo
```

If PowerShell blocks the activation script, you can avoid changing the execution policy:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\talend-api-starter.exe demo
```

## What success means

The demo writes two files and prints their paths:

```text
demo-output/local_view.json
demo-output/share_safe.json
```

Inspect the public-facing projection:

```bash
python -m json.tool demo-output/share_safe.json
```

The precise JSON may evolve, but these boundaries should not:

- mode is clearly identified as demo or synthetic;
- no token or account is requested;
- no provider API call is made;
- no context value, connection value, SQL, Java, shell, raw XML, or raw log is printed;
- errors are safe to share only after you have still reviewed them for local paths or names.

The demo is a functional tour, not proof that your live Talend account or a remote GitHub repository is accessible.

## Verify the command surface

```bash
talend-api-starter --help
talend-api-starter demo --help
talend-api-starter github jobs --help
talend-api-starter cloud workspaces --help
talend-api-starter cloud tasks --help
talend-api-starter cloud runs --help
```

The CLI help in your checked-out revision is the source of truth for optional selectors and output flags.

## Next: inspect a public GitHub repository

Choose a repository you are authorized to inspect and a narrow path containing a Talend project. Public repositories do not require a GitHub token in this starter.

```bash
talend-api-starter github jobs OWNER/REPOSITORY \
  --ref main \
  --path-prefix path/to/talend-project/process
```

The scanner resolves `main` to a commit SHA before reading the tree and blobs. It does not clone the repository, run source code, or write the raw artifacts to disk. Read the [GitHub API workflow](github-api.md) before using a large repository.

## Next: read Talend Cloud metadata

Do not paste a token directly into the command line. Follow the environment-variable and exact-host setup in [Talend Cloud API setup](talend-cloud-api.md), then begin with:

```bash
talend-api-starter cloud workspaces
```

Live mode is local-only and GET-only. You must supply an account, license or trial, personal access token, roles, and API entitlements that permit the requested endpoint; this project supplies none of them.

## Stop and clean up

Deactivate the environment when finished:

```bash
deactivate
```

Unset the token variable described in the Talend Cloud guide before sharing a terminal session or shell history. Deleting `.venv` removes the local package environment; it does not revoke provider credentials. Revoke tokens in the provider UI if exposure is suspected.

## If something fails

Use [Troubleshooting](troubleshooting.md). Public issues may include a minimal synthetic reproduction and sanitized error category, but never include tokens, authorization headers, client files, raw `.item` / `.properties`, logs, private repository URLs, or tenant/workspace/run identifiers.
