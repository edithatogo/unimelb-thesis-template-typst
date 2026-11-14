# Quality gates and bounded testing

This is the applicability record for [issue #4](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/4).
The repository contains a Typst template, Python authoring/validation helpers,
shell scripts and GitHub Actions workflows. Its useful automated contracts are
source validation, helper behavior, successful compilation and readable PDFs.

## Applicability

| Requested control | Decision and implementation |
| --- | --- |
| Property-based tests | Warranted for the Python validation and CSV helper contracts. Ten seeded generated properties exercise valid and invalid data, permutation, duplicate detection, CSV normalization and TOML metadata. |
| Least privilege | Workflows default to `contents: read`. Checkouts do not persist credentials. Only the existing tag-triggered release job receives `contents: write`. |
| Concurrency | PR/main quality and compile runs cancel stale work. Release runs use tag-specific groups and do not cancel a release already running. |
| Immutable actions | Actions and reusable workflows use full commit SHAs. The standalone actionlint download is versioned and SHA-256 verified before execution. |
| Dependency updates | The existing shared Renovate preset owns updates. Explicit GitHub Actions digest pinning reinforces it. A second Dependabot configuration would duplicate that responsibility and is excluded. |
| CodeQL | Applicable to Python helpers and GitHub Actions, not Typst. The repository already has GitHub default setup for `python` and `actions`; a conflicting advanced workflow is excluded. See the execution-status qualification below. |
| Dependency review | PRs fail for newly introduced high or critical vulnerabilities in GitHub-supported dependency snapshots, including development and unknown scopes. This is not a Typst package-registry vulnerability audit. |
| Workflow lint | actionlint checks all workflow YAML, expressions and supported embedded shell checks. It runs on PRs, main, merge groups and the weekly lane. |
| Secret/privacy scan | The existing pinned Presidio/Gitleaks workflow remains an independent check. The separately owned offline-security proposal in PR #9 is outside this change. |

The repository is maintained by one person. Automated gates do not introduce
mandatory reviewers, CODEOWNERS approvals or team gates. Publishing remains
restricted to version tags.

## Local verification

Use Python 3.11 or newer, the exact Typst version declared in `typst.toml`,
qpdf and Poppler (`pdfinfo` and `pdftotext`). Hosted verification pins
Python 3.15.1 and Typst 0.15.1. Python validation and property tests require only
the standard library.

```sh
make verify
```

This command checks Python syntax, runs template structure/metadata validation
and the normal property corpus, then compiles both `thesis.typ` and
`sample-chapter.typ`. Each resulting PDF must exist, be nonempty, pass qpdf,
contain at least one page and contain extractable text. Missing executables,
compiler-version mismatches, nonzero exits and command timeouts fail the gate.
Each compile/PDF command has a 60-second timeout. Output is written under
`build/verification/`, with a JSON result and command logs.

The shared Typst workflow additionally checks formatting and compiles
the thesis under all four profiles: default, draft, screen and print. Its pinned
matrix now runs from `quality.yml`. The former `ci-cd.yml` controller was
disabled by GitHub for inactivity on 5 October 2026 and is retired to avoid
retaining a dormant gate or duplicating jobs if it is later re-enabled. The
shared implementation, profile inputs and artifacts are preserved. PDF
structural checks do not replace visual inspection
when making layout, typography or accessibility changes.

For source-only work:

```sh
make verify-source
```

The delimiter-count scan in `validate_template.py` is advisory because it is
not a Typst parser. A passing source-only command is not evidence that a thesis
compiles. `scripts/check_packages.py` is an advisory inventory helper, not an
upstream vulnerability or update check, and is not used to claim either gate.

## Generated properties and replay

The ten properties cover:

1. Valid abbreviation/glossary collections survive permutation without mutation.
2. Missing, blank and incorrectly typed required fields are rejected.
3. Non-list containers are rejected.
4. Mixed malformed entries return errors without crashing or mutating input.
5. Duplicated identities remain invalid after reordering.
6. Abbreviation CSV export/import preserves the declared normalized values.
7. Glossary CSV export/import preserves normalized values and related terms.
8. Valid TOML accepts key-order and whitespace variation.
9. Required package metadata rejects missing or incorrectly typed values.
10. Comments, unrelated tables and malformed TOML cannot supply package fields.

Normal execution uses seed `20261115`, 64 iterations per property and a
zero-failure threshold: 640 generated property iterations. Some iterations
exercise both abbreviation and glossary contracts. The larger scheduled/manual
corpus uses the same seed and 512 iterations per property: 5,120 iterations.

```sh
python3 tests/test_properties.py --seed 20261115 --cases 64 \
  --report build/property-tests.json

make test-properties-deep
```

The JSON report contains the seed, replay command, per-property iteration
counts, Python version, elapsed time, source SHA-256 hashes and failure details.
Failing subtests identify the case index and synthetic input. Ordinary harness
errors also produce a failed report. Empty, skipped or incompletely executed
suites fail. CLI bounds are 1–1,024 iterations per property, collections of
one to eight rows, bounded text and at most four related glossary terms.
Replay with the recorded seed, case count and recorded source revision.

CSV tests explicitly model the existing importer: outer whitespace is stripped,
and semicolons delimit related terms. Related-term test values therefore exclude
semicolons. Existing case-sensitive validation behavior is preserved.

These tests qualify the Python helper functions. The current
`manage_terms.py` Typst loader and sample-data CLI are not a real Typst
configuration parser; they are not represented as validated live-data paths.

## Runtime budgets and evidence

| Lane | Bound and failure rule | Retained evidence |
| --- | --- | --- |
| Workflow lint | 5-minute job; any lint error fails | Log, 14 days |
| Full verification | 15-minute job including installation; 60 seconds per compile/PDF command; zero property failures or skips | Property JSON, verification JSON, logs and PDFs, 14 days |
| Dependency review | 5-minute job; high/critical threshold; snapshot-warning retry bounded to 60 seconds | GitHub check output |
| Extended properties | Weekly Monday 04:17 UTC or manual; 10-minute job; 5,120 iterations, zero failures or skips | JSON and log, 30 days |
| Four-profile Typst compilation | Existing shared 30-minute job limit per profile | PDFs, 14 days |
| Privacy/secrets | Existing independent 30-minute job limit | Existing scanner evidence policy |

The extended corpus does not run on ordinary PRs. Evidence upload steps use
`always()` so ordinary test failures retain their diagnostics. Runner
cancellation or installation failure can prevent generation of a report; a
missing artifact is not a passing test.

## Acceptance and exclusions

Review the checks for the exact PR head before integration. The CodeQL default
setup was observed in [run 43604503605](https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43604503605)
with Python and Actions jobs queued when this change was prepared. Configuration
alone is not successful analysis; require completed CodeQL evidence and do not
represent that queued run as passing.

No load testing, distributed-system tests or service deployment lanes are
warranted for this template. Typst itself is outside CodeQL's language coverage.
The property suite is not a proof of all rendering combinations, a full Typst
fuzzer, a scientific-content validator or an accessibility conformance audit.
The normal compile/PDF lane requires the existing package/tool downloads and
is not described as offline security qualification.

No Conductor directory exists at the inspected baseline. This document records
the issue's scope, acceptance commands and exclusions without creating a
separate project-management system.
