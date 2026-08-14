# From the free CLI to Assistant for Talend

The free **Talend API + GitHub API CLI** gives developers a practical, bounded way to learn metadata access, inspect an authorized local Studio project, and explore supported artifacts in public GitHub repositories.

**Assistant for Talend** is the separate paid, private path for organizations whose questions require proprietary projects, cross-job semantics, migration decisions, data-quality evidence, or a customer-controlled deployment.

## Clear free/private boundary

| Need | Free public CLI | Paid private Assistant for Talend |
| --- | --- | --- |
| Learn read-only Talend API calls | Included for supported GET metadata | Included in discovery when relevant |
| Run a credential-free synthetic demo | Included | Not required |
| Inspect an authorized local Studio project | Bounded supported job structure | Can be extended under an approved private scope |
| Inspect public GitHub artifacts anonymously | Included | Private source may be possible after access/security review |
| Semantic job diff | Not included | Scoped comparison of supported artifacts/revisions |
| Cross-job dependency and impact analysis | Not included | Private dependency mapping and change-impact evidence |
| Migration-readiness assessment | Not included | Compatibility, risk, and remediation analysis with stated limits |
| Data-quality diagnostics | Not included | Source/schema/runtime evidence review under an agreed scope |
| Private repository or internal network | Not included | Possible after architecture and authorization review |
| Private/on-premises deployment | Not included | Designed around approved security and residency constraints |
| Organization-specific recommendations | Not included | Defined deliverables, evidence, assumptions, and limitations |

Availability, scope, pricing, deployment, data handling, and support terms are agreed separately. The public repository makes no SLA, compatibility, outcome, or migration-success guarantee.

## When the private path makes sense

The free CLI is the right starting point when you need to learn the interface, verify a bounded read workflow, or inspect non-sensitive source you can legally use.

Consider a private engagement when the decision depends on questions such as:

- Which jobs will be affected by this repository or context change?
- Which components or patterns create the highest migration risk?
- Where do schema drift and data-quality failures enter the flow?
- How should the analysis run inside our network without uploading source?
- What evidence should engineering, security, and management review before a migration?

## Start without sharing sensitive data

For a first, non-sensitive inquiry, open a GitHub Issue that contains only:

- the broad business question (for example, dependency, migration, or data quality);
- an approximate project-size band, not project or client names;
- high-level deployment constraints;
- the desired decision or deliverable;
- a request to establish a private contact path.

Do not attach files, screenshots, logs, outputs, identifiers, credentials, private URLs, or environment details. A public issue is only a non-sensitive introduction; it does not authorize access or analysis.

## Never send through public GitHub

Never put the following in an issue, pull request, gist, screenshot, or public link:

- PAT, SAT, password, cookie, authorization header, SSH key, or populated `.env`;
- client/employer files, screenshots, logs, reports, database extracts, or source archives;
- private repository, clone, tenant, workspace, project, task, run, host, or network identifiers;
- `.item`, `.properties`, `talend.project`, contexts, connections, SQL, generated Java, or job exports;
- personal, customer, employee, contract, incident, procurement, or production data.

A private engagement begins only after an approved private channel, explicit scope, authorization, and data-handling path exist.

## Independence notice

Assistant for Talend and this CLI are independent offerings. They are not Qlik products, do not imply Qlik affiliation, and do not replace provider support, licensing, or product entitlements. The paid scope focuses on customer-authorized engineering analysis and deployment.
