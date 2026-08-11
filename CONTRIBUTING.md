# Contributing

Thank you for helping make read-only Talend metadata exploration safer and easier to learn.

## Start with the public-data rule

Contributions must be reproducible with bundled fixtures or newly authored synthetic data. Do not open, attach, paste, commit, or link:

- tokens, passwords, cookies, authorization headers, SSH keys, or populated environment files;
- client/employer files, screenshots, logs, exports, reports, database data, or source archives;
- private repository/clone URLs or private Git references;
- live tenant, workspace, project, artifact, task, execution, user, or account identifiers;
- real `.item`, `.properties`, `talend.project`, context, connection, SQL, generated Java, or job files;
- personal, confidential, contractual, incident, or production information.

If a bug exists only with a private artifact, create the smallest legally shareable synthetic reproduction. If you cannot, do not file the artifact or its details publicly; use a [non-sensitive Discussion](https://github.com/emrekaany/talend-cloud-github-api-starter/discussions) only to ask whether a private handling path is available.

## Product invariants

A contribution must preserve these boundaries:

1. Live provider traffic is GET-only and endpoint/host allowlisted.
2. Tokens never enter command arguments, URLs, logs, exceptions, fixtures, or output.
3. GitHub source reads stay public, path-bounded, and pinned to one immutable revision.
4. XML is untrusted: no DTD, external entity, network resolution, or embedded execution.
5. SQL, Java, shell, mapper expressions, and jobs are data, never commands.
6. Share-safe output is an explicit allowlist model, not a serialized local view.
7. Budget, truncation, ambiguity, or unsupported format errors fail closed.
8. Tests do not call live providers by default.

A proposal to add mutation, hosted credential entry, private-repository auth, broad filesystem access, or source execution changes the product boundary. Discuss it first; it will not be accepted as a small feature patch.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest
talend-api-starter demo
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

Use mocked transports for provider behavior. Tests that require a real tenant, token, private repository, or unrestricted network do not belong in the default test suite.

## Change workflow

1. Search existing issues and documentation.
2. Open a sanitized issue for a meaningful behavior change when early alignment would help.
3. Keep the patch narrow and add tests for success, limits, and safe failure.
4. Update user documentation when command, output, environment, or boundary behavior changes.
5. Update [PROVENANCE.md](PROVENANCE.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) when source origin, fixtures, copied material, or dependencies change.
6. Run the test suite and the offline demo.
7. Review the complete diff for secrets, private names, paths, URLs, generated artifacts, and accidental client content.

## Fixtures

Fixture names must be generic and fictional. Use reserved example domains such as `example.invalid`; do not imitate a real company, environment, job, database, host, GUID, or employee. Generate fixtures from a written schema or from scratch, never by redacting a private file.

Redaction is not provenance. A scrubbed client artifact is still a client artifact and must not enter this repository.

## Dependency and source policy

- Prefer the smallest maintained dependency surface.
- Pin compatible version ranges deliberately.
- Record direct dependencies and their licenses in `THIRD_PARTY_NOTICES.md`.
- Link to public API documentation instead of copying large examples or prose.
- Do not port code, test data, strings, screenshots, or commit history from private Talend repositories.
- Do not describe the project as a formal clean-room implementation unless a separately documented legal process supports that claim.

## Pull request checklist

- [ ] The change preserves GET-only, local-first, bounded behavior.
- [ ] Tests use synthetic inputs and deny live network by default.
- [ ] No secret, client file, private URL/ID, log, screenshot, or real Talend artifact is included.
- [ ] New remote text is treated as untrusted and escaped/redacted where applicable.
- [ ] Documentation and `--help` agree with the implementation.
- [ ] Provenance and third-party notices are accurate.
- [ ] I reviewed the full diff and generated files before submission.

By contributing, you confirm that you have the right to submit the material under the repository's license and that it does not contain confidential or restricted content.
