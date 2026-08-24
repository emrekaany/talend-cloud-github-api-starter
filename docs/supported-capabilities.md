# Supported capabilities

This page is the scope contract for the free **Talend API + GitHub API CLI**. If a behavior is not listed as supported, treat it as unavailable rather than inferring it from a provider API.

## Modes

| Command | Supported input | Network | Credential | Output |
| --- | --- | --- | --- | --- |
| `talend-api demo` | Bundled synthetic API responses and Studio artifacts | None after installation | None | Synthetic local/share-safe summaries |
| `talend-api local jobs` | Authorized local directory plus bounded relative path | None | None | Safe structural metadata from supported local pairs |
| `talend-api github jobs` | Public `owner/repository`, ref, and required project path | Anonymous GitHub GET | None | Pinned revision and safe structural metadata |
| `talend-api talend ...` | Exact official regional API base URL and local bearer credential | GET to validated Talend host | Your own supported credential | Operational metadata visible to the caller |

There is no hosted credential or file-upload mode. Public GitHub is the only remote source-repository target in this starter.

## Supported Talend API metadata

Subject to the caller's account, region, subscription/trial, credential type, roles, and endpoint entitlements, the CLI is designed to read:

- workspaces;
- executable tasks;
- recent task execution records.

Only endpoint templates explicitly included in the application allowlist may be called. Provider response fields cannot create new call targets. The regional host must match `https://api.<region>.cloud.talend.com`.

This repository does not grant API access. PAT/SAT support and endpoint availability must be confirmed against current Qlik documentation and the caller's authorized account.

## Supported Talend Studio source metadata

For an authorized local project or public GitHub path, the CLI is designed to:

- discover bounded `.properties` and `.item` candidates below a required scope;
- resolve a descriptor's process reference to an exact artifact;
- validate supported filename/version and relationship evidence;
- report safe job/component structure in the permission-restricted local view;
- report only identity-free job/component counts and warning counts in share-safe output;
- isolate malformed or unsupported artifacts instead of executing or trusting their content.

GitHub mode additionally pins all accepted source to one immutable revision. Local mode validates path containment and does not invoke Git or Talend.

Talend formats vary across versions and project histories. Unknown, incomplete, contradictory, or ambiguous shapes are reported as unsupported; they are not guessed.

## Output contracts

| Output | Intended use | May contain | Must not contain |
| --- | --- | --- | --- |
| Local view | Inspection by the authorized local operator | Supported resource/job labels, IDs or paths needed by the command | Token, authorization header, raw source, embedded code values, raw logs |
| Share-safe summary | Candidate for a report after human review | Identity-free aggregate counts and allowlisted run status/type buckets | Names, descriptions, tags, raw/hashed identity, repository/ref/path/SHA, local root, timestamps, account identity, raw source |

Share-safe output is a separate allowlist model. It is not the local view with a few strings removed, and it is not automatically safe for public release without review.

## Intentionally unsupported

| Capability | Status | Reason |
| --- | --- | --- |
| Start, stop, pause, publish, update, or delete a task | Not supported | Mutation is outside the public contract |
| Upload a project, file, log, output, or fixture | Not supported | No hosted ingestion surface |
| Read business rows moving through a job | Not supported | Operational/source metadata is not business data |
| Execute SQL, Java, shell, mapper expressions, or Talend jobs | Not supported | Source is treated as untrusted data |
| Download Studio source through Talend API | Not supported | No verified operational-API source contract is assumed |
| Private GitHub, GitLab, or Bitbucket authentication | Not supported | Enterprise auth and private-network design remain separate |
| Deep semantic diff, lineage, dependency, migration, or data-quality analysis | Not in the free starter | Available only as separately scoped private work |
| Telemetry, analytics, or hosted token entry | Not included | Local-first operation does not require them |
| Qlik Talend CommandLine compatibility | Not claimed | `talend-api` is an independent Python CLI, not that separate Qlik product |

## Free repository does not mean free provider access

The repository itself has no paid feature gate. Provider access remains governed by each provider:

- Talend API may require an eligible paid account or trial, a supported PAT or SAT, roles, and endpoint-specific entitlements.
- GitHub currently permits 60 unauthenticated REST requests per hour per originating IP and applies additional limits; this CLI stops one scan at 40 requests.
- Network, proxy, egress, security-review, and enterprise-policy costs remain the user's responsibility.

The project does not resell, grant, or guarantee access to either provider and does not claim that default tests authenticated a live Talend tenant.
