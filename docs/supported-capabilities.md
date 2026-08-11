# Supported capabilities

This page is the scope contract for the free starter. If a behavior is not listed as supported, treat it as unavailable rather than inferring it from a provider API.

## Modes

| Mode | Supported input | Network | Credential | Output |
| --- | --- | --- | --- | --- |
| Offline demo | Bundled synthetic cloud responses and Studio artifacts | None after installation | None | Local and share-safe synthetic summaries |
| Public GitHub | Public `owner/repository`, ref, required Talend project path | GET requests to GitHub | None | Pinned revision and safe Studio structural metadata |
| Local Talend Cloud | Exact official API base URL and local personal access token | GET requests to the validated Talend Cloud host | Required | Operational metadata visible to the caller |

There is no hosted credential mode. Public GitHub repositories are the only Git provider target in this starter.

## Supported Talend Cloud metadata

Subject to the caller's account, region, roles, and endpoint entitlements, the CLI is designed to read:

- workspaces;
- executable tasks;
- recent task execution records.

Only endpoint templates explicitly included in the application allowlist may be called. Provider response fields do not create new call targets.

## Supported Studio source metadata

For a public GitHub repository and one immutable revision, the CLI is designed to:

- list bounded `.properties` and `.item` candidates below a required project path;
- resolve a descriptor's process reference to an exact artifact in the same tree;
- validate supported filename/version and XMI relationships;
- report job label/version/status, component types/names, source paths, and pinned revision details in the permission-restricted local view;
- report only identity-free job/component counts and a warning count in the share-safe view;
- isolate a malformed artifact instead of executing or trusting its content.

Talend formats vary across product versions and project histories. An unknown or ambiguous shape is reported as unsupported; it is not guessed.

## Output contracts

| Output | Intended use | May contain | Must not contain |
| --- | --- | --- | --- |
| Local view | Inspection in the caller's terminal | Resource names/IDs the caller can already access, subject to command support | Token, authorization header, raw source, embedded code, raw logs |
| Share-safe summary | Copying into a report or support discussion after human review | Identity-free aggregate counts and allowlisted run status/type buckets | Names/descriptions/tags, raw or hashed identity, repository/ref/path/SHA, timestamps, account identity, filesystem path, context/connection values, raw source |

Share-safe output is a separate allowlist model. It is not the local view with a few strings removed.

## Intentionally unsupported

| Capability | Status | Reason |
| --- | --- | --- |
| Start, stop, pause, publish, update, or delete a task | Not supported | Mutation is outside the public contract |
| Upload a project, file, log, or fixture | Not supported | No hosted ingestion surface |
| Read rows moving through a job | Not supported | Provider/source metadata is not business data |
| Execute SQL, Java, shell, mapper expressions, or Talend jobs | Not supported | Source is treated as untrusted data |
| Download Studio `.item` source from Talend Cloud | Not supported | No verified Cloud-source contract is assumed |
| Private GitHub, GitLab, or Bitbucket repositories | Not supported | Enterprise auth and private-network access stay outside v1 |
| Deep semantic diff, lineage, dependency, migration, or data-quality analysis | Not in the free starter | Available only as separately scoped private work |
| Telemetry or analytics | Not included | The starter is local-first and does not need usage tracking |

## Free does not mean every provider is free

The starter itself has no paid feature gate. Live provider access remains governed by the provider:

- Talend Cloud may require a paid account or eligible trial, plus a PAT and endpoint-specific permissions.
- GitHub permits unauthenticated requests to public resources but applies primary and secondary rate limits.
- Network, proxy, egress, and enterprise policy costs remain yours.

This repository does not resell, grant, or guarantee access to either provider.
