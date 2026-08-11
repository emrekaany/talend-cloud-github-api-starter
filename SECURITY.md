# Security policy

## Supported versions

Until stable releases exist, security fixes target the latest code on `main` and the latest published release when practical. Older commits, forks, and modified deployments are not supported automatically.

| Version | Security fixes |
| --- | --- |
| Latest release / `main` | Best effort |
| Older versions | Not guaranteed |

## Report a vulnerability privately

Do **not** open a public issue or Discussion for a suspected vulnerability.

1. Use GitHub private vulnerability reporting from this repository's **Security** tab if it is enabled.
2. If it is not enabled, do not disclose the vulnerability. Use [GitHub Discussions](https://github.com/emrekaany/talend-cloud-github-api-starter/discussions) only to request a private security channel; include no reproduction, affected endpoint, secret, identifier, file, log, or exploit detail.
3. Wait for an actual private handling path before sharing technical details.

Never send an active token, password, cookie, authorization header, private key, client file, real `.item` / `.properties`, live log, database data, private repository URL, tenant/resource ID, or production screenshot. Reproduce with synthetic data whenever possible.

If a secret may already be exposed, revoke or rotate it with the provider immediately; do not wait for a project response.

## Helpful report contents

- affected version or commit SHA;
- vulnerability class and impacted boundary;
- minimal steps using synthetic data;
- expected versus observed security behavior;
- whether the issue appears to have caused data exposure;
- a suggested mitigation, if known.

Do not run tests against infrastructure you do not own or have explicit permission to assess. Do not access, modify, retain, or disclose other users' data.

## Security boundaries worth reporting

- a non-GET or non-allowlisted network call;
- Talend authorization sent to an unapproved host or redirect;
- a token in logs, exceptions, output, URLs, command arguments, or fixtures;
- demo mode contacting Talend Cloud or GitHub;
- traversal outside the requested GitHub path or mixing revisions;
- DTD/external-entity resolution or execution of embedded source content;
- request/response/tree/blob budgets that can be bypassed;
- raw or excluded data entering share-safe output;
- dependency or packaging behavior that introduces an exploitable boundary break.

Provider account recovery, general access errors, undocumented Talend behavior, feature requests, and ordinary installation problems belong in [SUPPORT.md](SUPPORT.md) unless they expose a security weakness.

## Response process

Maintainers will assess reports as capacity allows, keep discussion private while risk remains, and coordinate a fix and disclosure proportionate to impact. This open-source project does not promise an SLA or bug bounty. Please avoid public disclosure until a reasonable remediation discussion has occurred, while recognizing that reporters retain their legal rights.

## Operational safety

- Use a dedicated, least-privilege PAT when the provider permits it.
- Run live mode only on a trusted local machine.
- Review source and dependency changes before upgrading.
- Keep `.env` and shell-history material out of commits.
- Inspect share-safe output before external sharing; structural metadata can remain sensitive.
- Follow Qlik, GitHub, employer, and client security policies in addition to this document.
