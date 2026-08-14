# Security policy

## Supported versions

Security fixes target the latest code on `main` and the latest published release when practical. Older commits, forks, and modified deployments are not supported automatically.

| Version | Security fixes |
| --- | --- |
| Latest release / `main` | Best effort |
| Older versions | Not guaranteed |

## Report a vulnerability privately

Do **not** open a public issue or pull request for a suspected vulnerability.

1. Use GitHub private vulnerability reporting from this repository's **Security** tab if it is enabled.
2. If private vulnerability reporting is unavailable, contact the maintainer only through a private channel the maintainer has already published. Do not invent or guess an address.
3. If no private maintainer channel is published, do not post technical details publicly. Wait until a private route is available.

Never send an active PAT/SAT, password, cookie, authorization header, private key, client file, real `.item` / `.properties`, output from a real project, live log, database data, private repository URL, tenant/resource ID, internal host, or production screenshot. Reproduce with synthetic data whenever possible.

If a credential may already be exposed, revoke or rotate it through the authorized provider interface immediately; do not wait for a project response.

## Helpful private report contents

- affected version or commit SHA;
- vulnerability class and impacted boundary;
- minimal steps using synthetic data;
- expected versus observed security behavior;
- whether the issue appears to have caused exposure;
- a suggested mitigation, if known.

Do not test infrastructure you do not own or have explicit permission to assess. Do not access, modify, retain, or disclose other users' data.

## Security boundaries worth reporting

- a non-GET or non-allowlisted network request;
- Talend authorization sent to an unapproved host or redirect;
- a credential in logs, exceptions, output, URLs, command arguments, or fixtures;
- demo or local-project mode contacting a provider;
- local path traversal outside the selected project/scope;
- GitHub traversal outside the requested path or mixing revisions;
- DTD/external-entity resolution or execution of embedded content;
- request, response, directory, tree, blob, XML, or byte budgets that can be bypassed;
- raw/excluded data entering share-safe output;
- packaging or dependency behavior that creates an exploitable boundary break.

Account recovery, ordinary access errors, provider entitlement questions, undocumented Talend behavior, feature requests, and installation problems belong in [SUPPORT.md](SUPPORT.md) unless they expose a security weakness.

## Response process

Maintainers will assess reports as capacity allows, keep discussion private while risk remains, and coordinate remediation/disclosure proportionate to impact. This open-source project promises no SLA or bug bounty. Please avoid public disclosure during a reasonable remediation discussion while retaining your applicable legal rights.

## Operational safety

- Confirm the credential type currently supported by the endpoint and use the narrowest account/role scope available.
- Run Talend API commands only on a trusted local machine.
- Use only local projects and public repositories you are authorized to inspect.
- Review source and dependency changes before upgrading.
- Keep populated `.env` files and shell-history material out of commits.
- Inspect even share-safe output before external sharing; aggregate structure can remain sensitive.
- Follow Qlik, GitHub, employer, client, and legal policies in addition to this document.
