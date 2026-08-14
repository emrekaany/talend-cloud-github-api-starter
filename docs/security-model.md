# Security model

The CLI is designed for bounded, read-only metadata discovery. It reduces common first-use risks; it does not make an untrusted project, tenant, repository, workstation, dependency, or network inherently safe.

## Security promises

| Area | Promise |
| --- | --- |
| Network methods | Live provider calls are GET-only and endpoint-allowlisted |
| Talend host | Exact HTTPS host must match `api.<region>.cloud.talend.com`; URL credentials, paths, queries, fragments, and custom ports are rejected |
| Redirects | Refused rather than followed |
| Credentials | Talend bearer credential comes from the process environment, never a CLI argument |
| Offline modes | Demo and local-project inspection make no provider request |
| Local files | Scope is bounded and containment-checked; source content is never executed |
| Git consistency | Ref resolves once; tree and blobs remain tied to one immutable commit |
| Input size | Requests, responses, directories/files, tree entries, depth, blobs, bytes, and XML complexity are bounded |
| XML | DTD and external entities are rejected; no external resolution |
| Embedded content | SQL, Java, shell, mapper expressions, and jobs are never executed |
| Output | Share-safe records come from a separate explicit allowlist |
| Hosted ingestion | None; there is no public token or client-file upload form |
| Telemetry | None in the starter |

## Threats and controls

| Threat | Example | Control | Residual risk |
| --- | --- | --- | --- |
| Credential disclosure | Token appears in shell history or issue | Environment-only secret; redacted errors; reporting rules | Local malware, parent processes, or copy/paste can still expose it |
| SSRF / credential forwarding | Provider redirects to another host | Exact host policy; redirects refused | Compromised DNS/TLS trust is outside application control |
| Local path escape | Selected scope reaches another directory | Resolved containment checks; no followed source execution | OS/filesystem races and same-user malicious processes remain possible |
| Resource exhaustion | Huge directory, tree, JSON, blob, or XML | Finite count/byte/depth/time budgets | Allowed limits still consume local resources |
| XML entity attack | `.item` contains DTD/entity references | DTD/entity rejection and no external resolution | Parser/library defects remain possible |
| Repository race | Branch moves during remote scan | Resolve once and fetch by commit/tree/blob SHA | The selected commit can still contain hostile input |
| Code execution | XML embeds shell, SQL, Java, or expressions | Treat as data; never invoke runtimes | Future contributors must preserve this invariant |
| Output leakage | Local identifiers copied into a ticket | Separate share-safe projection plus human review | Aggregate structure may still be commercially sensitive |

## Credential lifecycle

1. Confirm the credential type currently supported by the selected endpoint and your account. Qlik may document PAT, SAT, or endpoint-specific requirements.
2. Create the narrowest credential and role scope available for the metadata you need.
3. Put the bearer value only in `TALEND_TOKEN` for the local process/session.
4. Put the exact regional API root in `TALEND_BASE_URL`; it must match `https://api.<region>.cloud.talend.com` with no extra URL components.
5. Run only the required `talend-api talend ...` command.
6. Unset the environment variables when finished.
7. Revoke or rotate a credential immediately if it enters a transcript, screenshot, log, issue, chat, or commit.

The application cannot prevent a parent process, debugger, endpoint-security product, or compromised workstation from reading process memory or environment. Use a trusted machine.

## Local project handling

- Use only a directory you own or are authorized to inspect.
- Keep `--path-prefix` as narrow as practical, normally the Talend project's `process` directory.
- The scanner selects supported `.properties` / `.item` candidates; it does not launch Talend, Git, interpreters, or project scripts.
- Raw artifacts are parsed as untrusted bytes and are not part of the documented JSON output.
- Do not use real client/employer artifacts to build public fixtures or bug reports, even after redaction.

## GitHub handling

- Public repositories only; requests are anonymous.
- A repository path is required and should be as narrow as practical.
- No clone, checkout, submodule traversal, workflow trigger, or working-tree execution.
- Selected artifacts remain tied to one immutable commit.
- Pair and supported-schema validation happen before a success record is emitted.

Public visibility is not consent to misuse data. Follow the source repository's license and all applicable employer, client, contractual, and legal obligations.

## Output safety

`local_view` and `share_safe` serve different audiences:

- local view may contain metadata already visible to the authorized operator;
- share-safe output removes identity and retains only allowlisted aggregates.

Neither label means “safe for the internet” without human review. Aggregate counts and recognized status/type buckets can reveal architecture.

Write outputs below a directory controlled by the current user. The CLI rejects unsafe output indirection and applies restrictive POSIX modes where available; Windows enforcement remains filesystem/DACL dependent. Files are written atomically, but a same-user malicious process remains outside the CLI's isolation boundary.

## Fail-closed events

The command stops or isolates the affected artifact when it encounters:

- a non-GET or non-allowlisted network target;
- a redirect;
- an exceeded request, response, tree, directory, depth, file, byte, XML, or time budget;
- a truncated/incomplete Git tree;
- a path escape, unsafe file type, or unsupported Git object;
- invalid JSON, base64, encoding, XML, or relationship evidence;
- ambiguous `.properties` / `.item` pairing.

No success result should imply completeness after one of these events.

## Out of scope

- security of Qlik, GitHub, the workstation, proxy, DNS, TLS trust, Python package index, or operating system;
- tenant identity governance and least-privilege role design;
- malware scanning of arbitrary repositories;
- enterprise private-network deployment;
- penetration testing or formal certification;
- mutation safety, because mutation is not implemented;
- compatibility with Qlik's separate Talend CommandLine product.

For vulnerability reporting, follow [SECURITY.md](../SECURITY.md). Never disclose a vulnerability, secret, client artifact, real output, or live identifier in a public issue.
