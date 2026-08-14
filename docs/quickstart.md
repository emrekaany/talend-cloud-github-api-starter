# Quickstart: Talend API + GitHub API CLI

Run the synthetic demo first. It verifies the installed package, `talend-api` command, safe parser, and output policy without asking for an account or token.

`talend-api` is this repository's independent Python CLI. It is not Qlik's separate Talend CommandLine product.

## Before you start

You need:

- Python 3.10 or newer;
- Git, or a downloaded copy of the repository;
- a terminal on macOS, Linux, or Windows.

The initial install may download Python packages. After installation, `demo` uses only bundled synthetic metadata and `.item` / `.properties` fixtures. It makes no Talend or GitHub API request.

## macOS or Linux

```bash
cd <cloned-repository>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
talend-api demo
```

## Windows PowerShell

```powershell
Set-Location <cloned-repository>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
talend-api demo
```

If PowerShell blocks the activation script, use the environment executables directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\talend-api.exe demo
```

## What demo success means

The command prints two completed output paths:

```text
demo-output/local_view.json
demo-output/share_safe.json
```

Inspect the identity-free projection:

```bash
python -m json.tool demo-output/share_safe.json
```

Demo success proves only the offline package path in your installed revision. It does not prove access to a live Talend account or remote GitHub repository.

The demo contract is:

- no token or account is requested;
- no provider request is made;
- every input is synthetic;
- no context value, connection value, SQL, Java, shell, raw XML, or raw log is printed;
- both output files still require handling appropriate to their source and audience.

## Verify the command surface

```bash
talend-api --help
talend-api demo --help
talend-api local jobs --help
talend-api github jobs --help
talend-api talend workspaces --help
talend-api talend tasks --help
talend-api talend runs --help
```

The help in your installed revision is the source of truth for optional selectors, budgets, and output flags.

## Inspect a local Talend Studio project

Choose a local project you own or are authorized to inspect. Point `PATH` to the project root and keep the prefix on its job directory:

```bash
talend-api local jobs /path/to/TALEND_PROJECT \
  --path-prefix process
```

This path:

- makes no provider request and needs no token;
- reads only supported `.properties` / `.item` candidates below the selected scope;
- treats XML and embedded SQL, Java, shell, and expressions as untrusted data;
- does not run Talend, Git, project scripts, or job code;
- writes the same separated local/share-safe output classes used by the other modes.

Do not point it at a client or employer project unless you have explicit authorization. Never attach real project files or generated output to a public issue.

## Inspect a public GitHub repository

Choose a public repository you are authorized to inspect and a narrow path containing a Talend project:

```bash
talend-api github jobs OWNER/REPOSITORY \
  --ref main \
  --path-prefix path/to/talend-project/process
```

The GitHub path is anonymous. It resolves the ref to a commit SHA before reading bounded tree/blob metadata, and it does not clone or execute repository content. Read [GitHub API workflow](github-api.md) before selecting a large repository.

## Read Talend API metadata

Live Talend API use is optional and requires your own eligible account, supported credential, roles, and endpoint entitlement. This free repository does not provide any of them.

Talend API is hosted at a regional endpoint shaped like `https://api.<region>.cloud.talend.com`. Follow [Talend API setup](talend-api.md) to put the exact host and token in local process environment variables. Do not paste a token into a command argument.

Then begin with:

```bash
talend-api talend workspaces
```

The three Talend commands are GET-only:

```bash
talend-api talend workspaces --help
talend-api talend tasks --help
talend-api talend runs --help
```

The default automated tests use synthetic fixtures and mocked transports. They do not authenticate a real Talend tenant, so a test pass cannot guarantee your subscription, region, credential type, role, or endpoint access.

## Stop and clean up

Deactivate the environment when finished:

```bash
deactivate
```

Unset any Talend credential variables before sharing a terminal session or shell transcript. Deleting `.venv` removes the local package environment; it does not revoke a provider credential. Revoke an exposed token in the provider interface immediately.

## If something fails

Read [Troubleshooting](troubleshooting.md). A public issue may include a package version, operating system, redacted error category, and steps based only on bundled or newly authored synthetic data. Never include secrets, provider response bodies, environment dumps, real `.item` / `.properties`, outputs from a real project, logs, private URLs, or live tenant/workspace/task/run identifiers.
