# Contributing

Thank you for helping make Talend API and Studio-metadata exploration safer and easier to learn from the command line.

## Public-data rule

Every contribution must be reproducible with bundled fixtures or newly authored synthetic data. Do not open, attach, paste, commit, or link:

- PATs, SATs, passwords, cookies, authorization headers, SSH keys, or populated environment files;
- client/employer files, screenshots, logs, outputs, exports, reports, database data, or source archives;
- private repository/clone URLs, private Git refs, local private paths, or internal hosts;
- live tenant, workspace, project, artifact, task, run, user, or account identifiers;
- real `.item`, `.properties`, `talend.project`, context, connection, SQL, generated Java, or job files;
- personal, confidential, contractual, incident, procurement, or production information.

If a behavior appears only with a private artifact, create the smallest newly authored synthetic reproduction. If you cannot, do not file the artifact or its details publicly. Suspected vulnerabilities follow [SECURITY.md](SECURITY.md).

## Product identity

The visible product is **Talend API + GitHub API CLI** and the canonical executable is `talend-api`. It is an independent Python project, not Qlik's separate Talend CommandLine product. Contributions must not imply affiliation, endorsement, free provider access, or live-account verification that did not happen.

## Product invariants

A contribution must preserve these boundaries:

1. Live provider traffic is GET-only and host/endpoint allowlisted.
2. Demo and local-project commands make no provider request.
3. Tokens never enter command arguments, URLs, logs, exceptions, fixtures, or output.
4. Local reads remain path-contained, bounded, and non-executing.
5. GitHub reads remain anonymous/public, path-bounded, and pinned to one immutable revision.
6. XML is untrusted: no DTD, external entity, external resolution, or embedded execution.
7. SQL, Java, shell, mapper expressions, and jobs are data, never commands.
8. Share-safe output is an explicit allowlist model, not a serialized local view.
9. Budget, truncation, ambiguity, and unsupported-format errors fail closed.
10. Default tests do not call live providers or require a real credential.

Mutation, hosted credential/file entry, private-repository auth, broad filesystem access, source execution, or Talend CommandLine compatibility would change the product boundary. Start a non-sensitive [Discussion](https://github.com/emrekaany/talend-cloud-github-api-starter/discussions) before proposing such a redesign; never include real environment details.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest --cov=talend_api_starter --cov-branch --cov-fail-under=100
talend-api demo
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest --cov=talend_api_starter --cov-branch --cov-fail-under=100
talend-api demo
```

If PowerShell blocks activation, replace each `python -m` prefix above with
`.\.venv\Scripts\python.exe -m`, and run
`.\.venv\Scripts\talend-api.exe demo`. Do not change the machine's execution
policy just to work on this project.

Use synthetic files and mocked HTTP transports. Tests that require a real tenant, PAT/SAT, private repository, client project, or unrestricted network do not belong in the default suite.

## Change workflow

1. Search existing issues and documentation.
2. Open a sanitized issue when early alignment on a behavior change would help.
3. Keep the patch narrow and add tests for success, enforced limits, and safe failure.
4. Update user documentation when command, output, environment, or boundary behavior changes.
5. Update [PROVENANCE.md](PROVENANCE.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) when source origin, fixtures, copied public material, or dependencies change.
6. Run the complete local checks and offline demo.
7. Review the complete diff for secrets, private names/paths/URLs, generated artifacts, and accidental client content.

## Fixtures and provenance

Fixture names must be generic and fictional. Use reserved domains such as `example.invalid`; do not imitate a real organization, environment, job, database, host, identifier, or person. Generate fixtures from a written schema or from scratch, never by redacting a private file.

Redaction is not provenance. A scrubbed client artifact is still a client artifact and must not enter the repository.

Behavior observed in repositories the contributor owns may inform a requirement or test scenario, but the public implementation and fixtures must be independently authored and legally publishable. Do not port proprietary code, test data, strings, screenshots, or commit history. Do not describe the work as a formal clean-room implementation unless a separately documented legal process supports that claim.

## Dependency policy

- Prefer the smallest maintained dependency surface.
- Pin compatible ranges deliberately.
- Record direct dependencies and licenses in `THIRD_PARTY_NOTICES.md`.
- Link to public API documentation instead of copying large examples or prose.

## Pull request checklist

- [ ] The change preserves GET-only, local-first, bounded behavior.
- [ ] Tests use synthetic inputs and deny live network by default.
- [ ] No secret, client file, private URL/ID, output, screenshot, log, or real Talend artifact is included.
- [ ] Remote text and local XML remain untrusted and non-executing.
- [ ] Documentation and `talend-api --help` agree.
- [ ] No claim implies a real Talend tenant was authenticated unless separately authorized and documented outside public artifacts.
- [ ] Provenance and third-party notices are accurate.
- [ ] The complete diff and generated files were reviewed before submission.

By contributing, you confirm that you have the right to submit the material under the repository license and that it contains no confidential or restricted content.
