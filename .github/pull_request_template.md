## What changed

<!-- Explain the user-facing or developer-facing change. -->

## Why

<!-- Explain the problem or learning goal this solves. -->

## Safety and provenance

- [ ] The change remains read-only and does not add Talend/GitHub mutations.
- [ ] No customer, employer, or private-repository artefact is included.
- [ ] No token, connection value, SQL, log, or internal URL is included.
- [ ] New fixtures are synthetic and documented in `PROVENANCE.md`.
- [ ] Remote text cannot become executable content or leak into share-safe output.

## Validation

- [ ] `python -m ruff format --check .`
- [ ] `python -m ruff check .`
- [ ] `python -m mypy src`
- [ ] `python -m pytest`
