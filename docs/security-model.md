# Security model

The starter is designed for bounded, read-only metadata discovery. It reduces the number of ways a first exploration can go wrong; it does not make an untrusted tenant, repository, workstation, dependency, or network inherently safe.

## Security promises

| Area | Promise |
| --- | --- |
| Network methods | Live provider calls are GET-only and endpoint-allowlisted |
| Talend hosts | Exact HTTPS host must match `api.<region>.cloud.talend.com`; paths, queries, credentials, and custom ports are rejected |
| Redirects | Refused rather than followed |
| Credentials | Talend PAT comes from the process environment, never a CLI argument |
| Git consistency | Ref resolves once; tree and blobs remain tied to one commit |
| Input size | Requests, responses, tree entries, depth, blob count, and bytes are bounded |
| XML | DTD and external entities are rejected; no network resolution |
| Embedded content | SQL, Java, shell, mapper expressions, and jobs are never executed |
| Output | Share-safe records come from an explicit allowlist |
| Hosted ingestion | None; there is no public token or client-file upload form |
| Telemetry | None in the starter |

## Threats and controls

| Threat | Example | Control | Residual risk |
| --- | --- | --- | --- |
| Credential disclosure | Token appears in shell history or an issue | Environment-only PAT; redacted errors; reporting warnings | Local malware, shell tooling, or user copy/paste can still expose it |
| SSRF / credential forwarding | Response redirects to another host | Exact host allowlist; redirects refused | Compromised DNS/TLS trust remains outside application control |
| Resource exhaustion | Huge tree, JSON body, or blob | Request/byte/depth/entry/blob budgets and finite timeouts | Allowed limits can still consume local resources |
| XML entity attack | Remote `.item` contains DTD/entity references | DTD/entity rejection and no external resolution | Parser/library defects remain possible |
| Repository race | Branch moves between tree and blob reads | Resolve once and fetch by commit/tree/blob SHA | The selected commit can still contain malicious input |
| Code execution | XML embeds shell, SQL, Java, or expressions | Treat as data; never invoke interpreters or Talend runtime | Future contributors must preserve this boundary |
| Output leakage | Local names/IDs copied into a ticket | Separate share-safe projection plus human-review warning | Structural metadata may still be commercially sensitive |

## Credential lifecycle

1. Create the narrowest PAT the provider supports for the endpoints you need.
2. Put it only in `TALEND_TOKEN` for the local process or session.
3. Put the exact provider API root in `TALEND_BASE_URL`; it must match `https://api.<region>.cloud.talend.com` and contain no path, query, fragment, credentials, or custom port.
4. Run only the required command.
5. Unset the environment variables when finished.
6. Revoke the PAT immediately if it enters a shell transcript, screenshot, log, issue, chat, or commit.

The application cannot prevent a parent process, debugger, endpoint-security product, or compromised workstation from reading process memory/environment. Use a trusted machine.

## GitHub source handling

- Public repositories only.
- Required repository path should be as narrow as practical.
- No clone, checkout, submodule traversal, or working-tree execution.
- Only `.item` and `.properties` blobs selected by the bounded tree walk are decoded.
- Raw artifacts remain in memory for parsing and are not intentionally persisted.
- Pairing and supported-schema validation happen before a success record is emitted.

Public visibility is not consent to misuse data. Apply repository licenses, employer policy, client contracts, and applicable law.

## Output safety

`local_view` and `share_safe` are different use cases:

- A local view may contain metadata already visible to the authorized caller.
- A share-safe view removes identities entirely and keeps only aggregate counts plus allowlisted run status/type buckets.

Neither label means "safe for the internet" without review. Recognized run status/type buckets and aggregate counts can reveal architecture. Treat outputs according to the source owner's policy.

Write outputs only below a directory controlled by your current user. The CLI rejects a symlink/junction destination and, on POSIX, group/world-writable non-sticky parents and output directories. POSIX file modes are enforced where available; Windows permissions remain filesystem/DACL dependent. Each JSON file is replaced atomically, but the two-file bundle is not a transactional database snapshot, so consumers should read it only after the command reports success. A malicious process already running as the same operating-system user remains outside this local CLI's isolation boundary.

## Fail-closed events

The operation should stop or isolate the affected artifact when it encounters:

- a non-GET or non-allowlisted target;
- a redirect;
- an exceeded request, byte, tree, depth, file, or time budget;
- a truncated/incomplete tree response;
- a path traversal pattern or unsupported Git object;
- invalid JSON, base64, encoding, size, XML, or relationship evidence;
- ambiguous `.properties` / `.item` pairing.

No success result should imply completeness after one of these events.

## Out of scope

- security of Qlik, Talend Cloud, GitHub, your workstation, proxy, DNS, or Python package index;
- identity governance and least-privilege role design for a tenant;
- malware scanning of arbitrary repositories;
- enterprise private-network deployment;
- penetration testing or formal certification;
- mutation safety, because mutation is not implemented.

For vulnerability reporting, follow [SECURITY.md](../SECURITY.md). Never disclose a vulnerability, secret, client artifact, or live identifier in a public issue.
