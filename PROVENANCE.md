# Provenance

This repository is an independent reimplementation created for the public project `talend-cloud-github-api-starter`. It is not described as a formal clean-room implementation.

## Origin policy

- No source code, fixture, snapshot, screenshot, report, documentation text, distinctive string, or Git history is to be copied from a private Talend repository.
- Real client, employer, employee, tenant, job, database, host, repository, GUID, log, or artifact data is not permitted.
- Synthetic fixtures must be authored from scratch from a written schema or generator, not produced by redacting a private file.
- Public API documentation may inform behavior; links and factual interfaces are referenced rather than reproducing provider examples or prose.
- Contributors must have the right to license submitted material under this repository's license.

## Artifact groups

| Group | Origin | Review status |
| --- | --- | --- |
| `src/` and `tests/` | Independently authored for this repository from the public scope and provider API contracts | Reviewed for v0.1.0 with automated tests and public-safety string scans |
| Synthetic `examples/` / fixtures | Generated or hand-authored fictional data for this repository | Reviewed for private names, IDs, paths, hosts, and structural copying in v0.1.0 |
| `README.md`, `docs/`, and root policies | Original explanatory material written for this repository | Reviewed for public boundaries, attribution, and unsupported claims in v0.1.0 |
| `assets/hero.svg`, `assets/social-preview.svg`, and the rasterized `assets/social-preview.png` | Original brand-neutral artwork created for this repository | Reviewed in v0.1.0; contain no provider logo or copied visual asset |
| Packaging and GitHub automation | Conventional project configuration authored for this repository | Direct dependencies/licenses reviewed and Actions pinned to immutable commits for v0.1.0 |

The status above records intended origin, not a legal opinion or proof that every future contribution is compliant.

## Public references used as specifications

- [Talend Cloud API authentication](https://help.qlik.com/talend/en-US/api-user-guide/Cloud/authentication)
- [Talend Cloud application URL mapping](https://help.qlik.com/talend/en-US/installation-guide-windows/Cloud/talend-cloud-application-url)
- [Talend API versioning policy](https://talend.qlik.dev/api-versioning-policy/)
- [Talend Cloud Orchestration API](https://talend.qlik.dev/apis/orchestration/2021-03/)
- [Talend Cloud Processing API](https://talend.qlik.dev/apis/processing/2021-03/)
- [GitHub REST API documentation](https://docs.github.com/en/rest)
- [GitHub REST API versioning](https://docs.github.com/en/rest/about-the-rest-api/api-versions)
- [Qlik trademarks](https://www.qlik.com/us/legal/trademarks)

These references define public interfaces or legal naming context. Their documentation, code samples, logos, and assets are not relicensed by this repository.

## Release review

Before a public release:

1. review every tracked file and Git object for secrets and non-public material;
2. scan for private project names, paths, domains, GUIDs, emails, account/resource IDs, and distinctive strings;
3. confirm fixtures are synthetic at source, not merely redacted;
4. inspect dependency and action licenses/notices;
5. verify README commands against the released CLI;
6. confirm trademark placement and the not-affiliated disclaimer;
7. record any third-party code or assets in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md);
8. obtain any employer/IP, repository-name, license, CTA, and publication approvals required outside this repository.

## Updating this record

Any contribution that changes origin, imports a snippet, adds generated material, or introduces a dependency must update this file or `THIRD_PARTY_NOTICES.md` in the same pull request. When provenance cannot be established, do not merge the material.

Last documentation review: 2026-08-11.
