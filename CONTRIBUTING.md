# Contributing

Work from the current default branch and check open PRs for overlapping changes.
Keep each PR focused, link its issue and explain any changes to thesis output.

## Set up

Use Python 3.11 or newer (CI uses 3.15.1), GNU Make, Typst 0.15.1,
qpdf and Poppler's `pdftotext` and `pdfinfo`. The Typst version is also recorded
in `typst.toml`; keep the build workflows consistent with it.

For coverage, install the pinned development dependency in an isolated environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

## Validate

Run from the repository root:

```sh
make verify
make coverage
```

`make verify` runs unit tests, template structure and package checks, desired
ruleset validation, bounded properties, and thesis/sample compilation with PDF
validation. The existing Typst CI separately runs typstyle 0.15.0 and the four
thesis build profiles. Errors stop the run.

For a focused iteration, use `make verify-python`, `make verify-source` or
`make verify-typst`. See [Quality gates](docs/quality-gates.md) for property replay.
These narrower commands do not replace the complete check before a change is
reported as verified. Inspect the affected rendered pages for layout changes.

Coverage reports measure line and branch execution in `scripts/preflight.py`,
`scripts/validate_template.py` and `scripts/check_repository_policy.py`.
They do not measure Typst source, visual fidelity or the other helper scripts.

## Pull requests

Include the problem, resulting behavior, commands and results, commit SHA and
hosted CI links. Describe any checks that could not run. Use synthetic examples;
sanitize logs and screenshots before attaching them. Do not include private
theses, research data or credentials.

Keep mandatory human approvals at zero: automated checks provide the merge gate.
Keep action pins, privacy checks and tag-only publication intact. Changes to
repository settings need live verification; validating a JSON file is insufficient.

Renovate inherits `github>edithatogo/renovate-config`; its
[Dependency Dashboard](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/7)
records discovered dependencies and pending updates. Avoid competing update bots.

Read [AGENTS.md](AGENTS.md), [SECURITY.md](SECURITY.md) and
[the maintenance guide](docs/maintenance.md) for the applicable safeguards.
