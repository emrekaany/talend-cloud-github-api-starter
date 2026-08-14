# Support

## Fastest safe path

1. Run `talend-api demo`.
2. Read [Troubleshooting](docs/troubleshooting.md).
3. Search existing GitHub Issues.
4. If the problem is reproducible with bundled or newly authored synthetic data, open the appropriate issue form.

Community support is best effort. The free CLI has no guaranteed response time, compatibility commitment, provider escalation, or production SLA.

## Channels

| Need | Channel |
| --- | --- |
| Reproducible bug using bundled/synthetic data | GitHub bug-report issue form |
| Documentation correction | GitHub documentation issue form |
| Read-only feature proposal | GitHub feature-request issue form |
| Non-sensitive usage question | GitHub Issue with a synthetic example |
| Suspected vulnerability | Private route in [SECURITY.md](SECURITY.md); never a public issue |
| Private semantic diff, dependency, migration, data-quality, or deployment work | Follow the non-sensitive introduction in [Assistant for Talend](docs/services.md) |

## Never post publicly

Do not put these in an issue, pull request, gist, screenshot, or linked document:

- PAT, SAT, password, cookie, authorization header, SSH key, or environment dump;
- client/employer file, log, output, report, screenshot, database content, or source archive;
- private repository/clone URL, private ref, local private path, or internal host;
- live tenant, workspace, project, artifact, task, run, user, or account ID;
- real `.item`, `.properties`, `talend.project`, context, connection, SQL, generated Java, or job content;
- personal, customer, employee, contract, incident, procurement, or production information.

Redacting a real client file does not make it acceptable for a public issue. Create a new synthetic reproduction.

## Public maintainers can help with

- installation and `talend-api` behavior on supported Python versions;
- offline demo failures;
- bounded local-project behavior reproduced with synthetic files;
- anonymous public-GitHub inspection using non-sensitive repositories;
- documented Talend API configuration and safe error categories;
- documentation, synthetic fixtures, and read-only feature proposals.

## Public maintainers cannot provide

- Talend accounts, trials, licenses, roles, PATs, SATs, or endpoint entitlements;
- proof that a live tenant accepts a credential or exposes an endpoint;
- GitHub account recovery or rate-limit exceptions;
- access to private repositories or enterprise networks;
- diagnosis from client source, live logs, credentials, outputs, or production data;
- official Qlik support, warranty, or Talend CommandLine support;
- emergency production operations.

For provider account, licensing, entitlement, or product issues, use the provider's official support channel. This independent project is not affiliated with, sponsored by, or endorsed by Qlik.
