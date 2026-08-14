# Provenance

This repository is an independent reimplementation created for the public project `talend-api-github-cli`. It is not described as a formal clean-room implementation.

## Origin policy

- No source code, fixture, snapshot, screenshot, report, documentation text, distinctive string, or Git history is to be copied from a private Talend repository.
- Real client, employer, employee, tenant, job, database, host, repository, GUID, log, or artifact data is not permitted.
- Synthetic fixtures must be authored from scratch from a written schema or generator, not produced by redacting a private file.
- Public API documentation may inform behavior; links and factual interfaces are referenced rather than reproducing provider examples or prose.
- Contributors must have the right to license submitted material under this repository's license.

## Artifact groups

| Group | Origin | Review status |
| --- | --- | --- |
| `src/` and `tests/` | Independently authored for this repository from public provider contracts and the behavior-only validation record below | Reviewed for the local v0.2.0 candidate with automated tests and public-safety scans |
| Synthetic `examples/` / fixtures | Generated or hand-authored fictional data for this repository | Reviewed for private names, IDs, paths, hosts, and structural copying in the local v0.2.0 candidate |
| `README.md`, `docs/`, and root policies | Original explanatory material written for this repository | Reviewed for public boundaries, attribution, and unsupported claims in the local v0.2.0 candidate |
| `assets/hero.svg`, `assets/social-preview.svg`, and the rasterized `assets/social-preview.png` | Original brand-neutral artwork created for this repository | Re-rendered and reviewed for v0.2.0; contain no provider logo or copied visual asset |
| Packaging and GitHub automation | Conventional project configuration authored for this repository | Direct dependencies/licenses reviewed and Actions pinned to immutable commits |

The status above records intended origin, not a legal opinion or proof that every future contribution is compliant.

## Behavior-only validation against repositories we control

Before adding the local-project CLI, these user-controlled repositories were
reviewed read-only to confirm that the intended workflows already operate in
practice. Their code, Git history, fixtures, reports, logs, configuration, and
client artifacts were **not** copied into this public project.

| Maintainer-controlled source class | Behavior confirmed locally |
| --- | --- |
| Talend semantic-diff tool | Bounded Git/ref/path handling and safe Talend XML behavior |
| Talend project-assistant tool | Local `.item` / `.properties` discovery and parsing behavior |
| Read-only diagnostics tool | Pairing, XML safety, isolation, and redaction behavior |

Two reviewed packages declare proprietary licensing, and another has no
repository license. The reviewed projects also contain material unsuitable for
public distribution. Their names, remotes, commit IDs, files, and test data are
therefore intentionally absent from this public repository. The public
implementation uses newly authored source and synthetic fixtures while
preserving only independently observable behavioral requirements.

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

Last documentation review: 2026-08-13.
