# Assistant for Talend

The free starter is intentionally small: it teaches safe, read-only access to operational metadata and public Studio artifacts. **Assistant for Talend** is a separate paid, private offering for teams whose questions depend on proprietary projects, environment-specific semantics, or private deployment constraints.

## Free starter vs private engagement

| Need | Free public starter | Paid private Assistant for Talend |
| --- | --- | --- |
| Learn a GET-only metadata workflow | Included | Included as part of discovery when relevant |
| Run a credential-free synthetic demo | Included | Not required |
| Inspect public `.item` / `.properties` structure | Included | Can be extended to approved private sources |
| Semantic job diff | Not included | Scoped to supported Talend artifacts and revision pairs |
| Cross-job dependency analysis | Not included | Private dependency and impact mapping |
| Migration-readiness assessment | Not included | Evidence-based compatibility, risk, and remediation review |
| Data-quality diagnostics | Not included | Source/schema/runtime evidence review under a private scope |
| Private GitHub/GitLab/Bitbucket or internal network | Not included | Possible after architecture and access review |
| Private/on-premises deployment | Not included | Designed around the client's security and residency constraints |
| Organization-specific report and recommendations | Not included | Defined deliverable with explicit evidence and limitations |

Availability, scope, pricing, deployment model, data handling, and support terms are agreed separately. The public repository makes no SLA, outcome, compatibility, or migration-success guarantee.

## A sensible first conversation

A useful **non-sensitive** introduction can describe:

- the business question: semantic diff, dependency, migration, data quality, or private deployment;
- approximate project shape using broad bands rather than names or files;
- provider and deployment constraints at a high level;
- desired deliverable and decision date;
- whether a formal security/procurement review is required.

For that first conversation, use [GitHub Discussions](https://github.com/emrekaany/talend-cloud-github-api-starter/discussions). Keep the opening message non-sensitive and high-level.

## Do not send through public GitHub

Never put any of the following in an issue, Discussion, pull request, gist, or other public channel:

- access token, password, cookie, authorization header, SSH key, or `.env` content;
- client/employer files, screenshots, logs, reports, database extracts, or source archives;
- private repository, clone, tenant, workspace, project, task, run, host, or network identifier;
- `.item`, `.properties`, `talend.project`, context, connection, SQL, generated Java, or job export;
- personal, customer, employee, or production data;
- contract, incident, vulnerability, or procurement material.

A private engagement starts only after an approved private channel, scope, authorization, and data-handling path exist. A public message does not authorize access, upload, analysis, or deployment.

## Product boundary

Assistant for Talend does not turn this starter into an unofficial Talend Cloud service and does not imply affiliation with Qlik. Provider support, licensing, and product defects remain with the provider. The private offering focuses on customer-authorized engineering analysis and deployment.
