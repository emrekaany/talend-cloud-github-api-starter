# Talend API + GitHub API — Free Read-Only CLI

<p align="center">
  <img src="assets/hero.png" alt="An independent Talend engineering toolkit: a free read-only CLI leading to three separately scoped private products" width="100%">
</p>

<p align="center">
  <strong>Inspect safely for free. Diagnose deeply in private.</strong><br>
  Local Studio · Public GitHub · Your authorized Talend API account
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/emrekaany/"><img src="https://img.shields.io/badge/Request-a%20private%20Talend%20assessment-2563eb?style=for-the-badge" alt="Request a private Talend assessment on LinkedIn"></a>
  <a href="#run-free"><img src="https://img.shields.io/badge/Run-the%20free%20demo-0f766e?style=for-the-badge" alt="Run the free demo"></a>
</p>

<p align="center">
  <a href="https://github.com/emrekaany/talend-cloud-github-api-starter/actions/workflows/ci.yml"><img src="https://github.com/emrekaany/talend-cloud-github-api-starter/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="https://github.com/emrekaany/talend-cloud-github-api-starter/actions/workflows/codeql.yml"><img src="https://github.com/emrekaany/talend-cloud-github-api-starter/actions/workflows/codeql.yml/badge.svg" alt="CodeQL status"></a>
  <img src="https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776AB?logo=python&amp;logoColor=white" alt="Python 3.10 through 3.14">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-64748b" alt="MIT license"></a>
</p>

<p align="center"><a href="docs/quickstart-tr.md">Türkçe</a> · <a href="docs/services.md">Private products</a> · <a href="https://github.com/emrekaany/talend-cloud-github-api-starter/discussions">Public discussion</a></p>

## Private Talend engineering

![Assistant for Talend, Column Diagnostics, and Talend Commit Diff](assets/product-strip.png)

- **Assistant for Talend** traces Job families and turns exact ETL, SQL, runtime, and risk evidence into prioritized guidance.
- **Column Diagnostics** catches Talend ↔ Oracle type, length, precision, nullability, and truncation risks before release.
- **Talend Commit Diff** compares immutable revisions, filters known serialization noise, and focuses regression testing on semantic change.

![A synthetic private-product finding with exact location, evidence, risk, and validation steps](assets/sample-finding.png)

These private products are separately scoped, customer-authorized, and designed for approved evidence. Deterministic local rules are available; an AI layer is optional.

<p align="center"><a href="docs/services.md"><strong>Explore the private toolkit →</strong></a></p>

## Run free

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "https://github.com/emrekaany/talend-cloud-github-api-starter/archive/refs/tags/v0.2.0.zip"
talend-api demo
```

No Talend account or token is required. The demo uses synthetic fixtures and makes no provider request. [Windows and full setup →](docs/quickstart.md)

| Read path | Needs |
| --- | --- |
| `talend-api demo` | Nothing |
| `talend-api local jobs …` | Authorized local Studio files |
| `talend-api github jobs …` | Public repo + exact ref/path |
| `talend-api talend workspaces` | Your endpoint + environment token |

> GET only · No job execution · No mutation · No business rows · No hosted upload · No telemetry

## Verified

![254 tests passed with 100 percent statement and branch coverage on Linux and Windows across Python 3.10 through 3.14](assets/verification-strip.png)

Current source: **254 credential-free tests passed**, plus one expected macOS filesystem skip. CI enforces **100% statement and branch coverage**. No live Talend tenant or entitlement was used for this verification.

[Security](docs/security-model.md) · [Architecture](docs/architecture.md) · [Talend API](docs/talend-api.md) · [GitHub API](docs/github-api.md) · [Examples](docs/examples.md) · [Changelog](CHANGELOG.md)

Never post credentials, source files, logs, screenshots, private URLs, client identifiers, or database details on public GitHub.

<sub>Independent MIT-licensed project. Not affiliated with, sponsored by, or endorsed by Qlik. Talend and Qlik are trademarks of their respective owners. Provider access and licenses are not included.</sub>
