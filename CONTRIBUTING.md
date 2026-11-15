# Contributing

Work from the current default branch and check open PRs for overlapping changes.
Keep each PR focused, link its issue and explain any changes to thesis output.

## Set up

Use Python 3.11 or newer (CI uses 3.15.1), GNU Make, Typst 0.15.1,
qpdf and Poppler's `pdftotext`, `pdfinfo` and `pdffonts`. The Typst version is also recorded
in `typst.toml`; keep the build workflows consistent with it.

Install the pinned validation and coverage dependencies in an isolated environment:

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
validation. It also checks 14 synthetic rendered specimens for declarations,
contributions, publication tables, footnotes and appendix references; see the
[COR-01 corpus](tests/rendered/cor01/README.md). The existing Typst CI separately runs typstyle 0.15.0 and the four
thesis build profiles. Errors stop the run.

For a focused iteration, use `make verify-python`, `make verify-source` or
`make verify-typst`. See [Quality gates](docs/quality-gates.md) for property replay.
These narrower commands do not replace the complete check before a change is
reported as verified. Inspect the affected rendered pages for layout changes.
The same canonical report includes the [bounded adapter](docs/typst-contract-adapter.md)
and [native evidence](docs/native-evidence.md) corpora; their separate acceptance
boundaries remain in force.

Coverage reports measure line and branch execution in `scripts/preflight.py`,
`scripts/validate_template.py`, `scripts/check_repository_policy.py`,
`scripts/thesis_contract.py`, `scripts/typst_contract_adapter.py`,
`scripts/native_evidence.py`, `scripts/package_template.py`,
`scripts/submission_policy.py` and `scripts/replay_build.py`.
They do not measure Typst source, visual fidelity or the other helper scripts.
The [local packaging corpus](docs/packaging.md) uses the same canonical watchdog;
its native archive/init/watch/PDF evidence is separate from helper coverage.
The [dated submission-policy gate](docs/submission-policy.md) checks 64 supplied-data
scenarios against a neutral PDF's actual bytes. These are data and artifact-binding
checks; institutional approval and rendered policy qualification remain unresolved.

The [bounded replay gate](docs/reproducible-builds.md) adds actual Linux network
namespace controls when invoked with
`make verify VERIFY_ARGS="--replay-package-cache /absolute/path/to/prepared-cache"`.
CI opts in with its explicit package cache after the ordinary online preparation
and document checks, selecting `--replay-isolation privileged-network`. Its
namespace setup drops privileges before project code; local verification keeps
the default unprivileged user/network backend. The isolated compiler never falls back to an online build.
A missing namespace capability fails the opted-in gate; the normal local command
records replay as unexecuted. Neither state supplies whole-thesis or release proof.

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

## Shared thesis contract

`make verify-contract` validates the versioned bundle, source snapshots, legacy
crosswalk, configuration fixtures and adapter-result bindings. It is part of
`make verify` and `make verify-python`. Read [the contract guide](docs/thesis-contract.md)
for typed CLI inputs, precedence, adapter pins, migration and the remaining
rendered-output qualification. Configuration validity does not certify a thesis.
