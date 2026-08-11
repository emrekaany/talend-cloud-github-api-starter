# Third-party notices

This file summarizes direct third-party dependencies and referenced product names. Each package remains governed by its own license; this summary does not replace the license text distributed by its author or a release-time dependency audit.

## Runtime dependencies

| Package | Declared range | License commonly published by project | Project |
| --- | --- | --- | --- |
| `httpx` | `>=0.27,<1` | BSD 3-Clause | [encode/httpx](https://github.com/encode/httpx) |
| `typer` | `>=0.12,<1` | MIT | [fastapi/typer](https://github.com/fastapi/typer) |

## Build and test dependencies

| Package | Declared range | License commonly published by project | Project |
| --- | --- | --- | --- |
| `hatchling` | `>=1.27` | MIT | [pypa/hatch](https://github.com/pypa/hatch) |
| `pytest` | `>=8,<10` | MIT | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| `pytest-cov` | `>=5,<8` | MIT | [pytest-dev/pytest-cov](https://github.com/pytest-dev/pytest-cov) |
| `mypy` | `>=1.14,<2` | MIT | [python/mypy](https://github.com/python/mypy) |
| `ruff` | `>=0.9,<1` | MIT | [astral-sh/ruff](https://github.com/astral-sh/ruff) |
| `build` | CI tool, version resolved at build time | MIT | [pypa/build](https://github.com/pypa/build) |

## GitHub Actions

| Action | Immutable release pin | License commonly published by project | Project |
| --- | --- | --- | --- |
| `actions/checkout` | `d23441a48e516b6c34aea4fa41551a30e30af803` (`v6`) | MIT | [actions/checkout](https://github.com/actions/checkout) |
| `actions/setup-python` | `ece7cb06caefa5fff74198d8649806c4678c61a1` (`v6`) | MIT | [actions/setup-python](https://github.com/actions/setup-python) |
| `github/codeql-action` | `5595ccaf912efad79be6eef63a5619ff05969be3` (`v4`) | MIT | [github/codeql-action](https://github.com/github/codeql-action) |

This GitHub source release does not vendor transitive Python dependencies. If a future binary, container, or other bundled distribution includes transitive dependencies, generate and review its complete resolved dependency/license inventory before publication. A version range or linked repository is not evidence that every resolved version has the same metadata.

## Provider documentation

The implementation and documentation link to public API references from GitHub and Qlik. Links and interface facts are used for interoperability; provider documentation text, examples, logos, and artwork are not included or relicensed.

## Trademarks

Qlik Talend Cloud® and Talend® are trademarks of QlikTech International AB or its affiliates. GitHub is a trademark of GitHub, Inc. All other trademarks are the property of their respective owners.

This independent project is not affiliated with, sponsored by, or endorsed by Qlik or GitHub. No provider logo is included in the repository's hero artwork.

## Project material

The brand-neutral SVG hero, documentation, and policy text are original project material as recorded in [PROVENANCE.md](PROVENANCE.md); they do not require an additional third-party notice.
