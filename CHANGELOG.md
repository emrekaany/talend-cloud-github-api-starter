# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Resolve a bare Git ref as a branch first and then as a tag when the branch is
  absent, while preserving explicit `refs/heads/...`, `refs/tags/...`, and
  commit-SHA behavior.
- Classify GitHub `502`, `503`, and `504` responses as temporary provider
  failures and retry them at most twice inside the existing request budget.

### Changed

- Add verified tagged-source and clone installation paths, a credential-free
  public smoke target, explicit anonymous rate-limit guidance, and current
  hosted-release evidence.
- Prepare package version `0.2.1`; the release tag and distribution-asset
  publication remain separate steps.

## [0.2.0] - 2026-08-14

### Changed

- Reposition the product as **Talend API + GitHub API CLI** and expose the
  canonical `talend-api` executable.
- Replace the visible `cloud` command group with
  `talend workspaces|tasks|runs`; keep the provider host requirement in the
  technical setup documentation.
- Rename the public JSON provider contract to `talend_api` and bump the output
  schema to `2.0`.

### Added

- Add `local jobs` for bounded, network-free inspection of a local Talend
  Studio project's `.properties` / `.item` pairs.
- Add clean-wheel CLI smoke coverage and `--version` support.

## [0.1.2] - 2026-08-11

### Fixed

- Reject Windows junction output destinations on Python 3.10 and newer by
  inspecting the `lstat()` reparse tag.
- Expand Windows smoke coverage to Python 3.10, 3.11, and 3.12.

## [0.1.1] - 2026-08-11

### Fixed

- Let Windows enforce the output directory ACL instead of applying POSIX-style
  file modes that do not model or strengthen Windows access control.

## [0.1.0] - 2026-08-11

### Added

- Credential-free offline demo with synthetic Talend metadata.
- GET-only Talend Cloud workspace, task, and execution inventory commands.
- Public GitHub job discovery pinned to an immutable commit and bounded path.
- Safe `.properties` / `.item` inspection with DTD and entity rejection.
- Separate local and share-safe output contracts.
- English and Turkish quickstarts, security documentation, and CI workflows.

[0.2.0]: https://github.com/emrekaany/talend-cloud-github-api-starter/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/emrekaany/talend-cloud-github-api-starter/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/emrekaany/talend-cloud-github-api-starter/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/emrekaany/talend-cloud-github-api-starter/releases/tag/v0.1.0
