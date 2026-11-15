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
| Dependency updates | The shared Renovate preset owns routine version updates, with explicit GitHub Actions digest pinning. A second Dependabot version-update configuration is excluded. Existing Dependabot security updates remain enabled until Renovate's effective vulnerability processing is qualified; no security-update handoff is claimed. |
| CodeQL | Applicable to Python helpers and GitHub Actions, not Typst. The repository already has GitHub default setup for `python` and `actions`; a conflicting advanced workflow is excluded. See the execution-status qualification below. |
| Dependency review | PRs fail for newly introduced high or critical vulnerabilities in GitHub-supported dependency snapshots, including development and unknown scopes. This is not a Typst package-registry vulnerability audit. |
| Workflow lint | actionlint checks all workflow YAML, expressions and supported embedded shell checks. It runs on PRs, main, merge groups and the weekly lane. |
| Secret/privacy scan | The existing pinned Presidio/Gitleaks workflow remains an independent check. The separately owned offline-security proposal in PR #9 is outside this change. |

The repository is maintained by one person. Automated gates do not introduce
mandatory reviewers, CODEOWNERS approvals or team gates. Publishing remains
restricted to version tags.

## Local verification

Use Python 3.11 or newer, the exact Typst version declared in `typst.toml`,
qpdf and Poppler (including `pdfinfo`, `pdftotext` and `pdffonts`). Hosted verification pins
Python 3.15.1 and Typst 0.15.1. Install the pinned Python dependencies from
`requirements-dev.txt`; the shared contract validator uses JSON Schema.

```sh
make verify
```

This command checks Python syntax, runs template structure/metadata validation,
the shared contract checks and the normal property corpus, then compiles both
`thesis.typ` and `sample-chapter.typ`. Each resulting PDF must exist, be nonempty, pass qpdf,
contain at least one page and contain extractable text. Missing executables,
compiler-version mismatches, nonzero exits and command timeouts fail the gate.
Each compile/PDF command has a 60-second timeout and a separate, bounded
five-second cleanup budget. POSIX commands run in their own session; a timeout
terminates the command group even if its leader has already exited. Five
maintenance tests exercise actual commands, diagnostics and descendant cleanup;
see [process timeouts](process-timeouts.md). Output is written under
`build/verification/`, with a JSON result and command logs.
The integrated maintenance increment adds unit tests, package checks and
desired-policy validation to the same command; see [maintenance](maintenance.md).

The bounded [COR-01 corpus](../tests/rendered/cor01/README.md) also runs through
this verifier. Its 14 synthetic specimens assert actual declaration clauses,
contribution/publication rows, footnote values and appendix-reference text.
Empty, one-entry and multiple-entry controls test absence and exact cardinality.
Each fixture has a separate raw-code control page; unwanted source fragments
are rejected only in the component region. The report retains exact commands,
tool identities, source/fixture/output hashes and failure diagnostics. These
checks establish the declared rendered-text behavior, not complete navigation,
accessibility, identity projection or institutional policy conformance.

The [COR-02 navigation corpus](../tests/rendered/cor02/README.md) then checks
three synthetic PDFs with independent heading, page-label and link expectations.
It parses native qpdf JSON and Poppler bounding boxes to match contents rows and
bookmarks to their visible destinations, including headings on the same page.
Direct appendix specimens exercise compatibility and continuous Arabic page
labels. These cases retain native sidecars, scoped oracle reports and the same
60-second command budget. See the [repair boundary](cor02-navigation.md) for
the reproduced defects and the remaining glossary, index and policy acceptance.

The same runner now includes the following bounded rendered checks. Every case
retains the input, fixture, tool and output digests; expected rejections and
failed privacy scans remain distinguishable from clean PDF results.

| Corpus | Cases | Checked behavior |
| --- | ---: | --- |
| [Configuration](cor03-configuration.md) | 34 | Resolved legacy options, typed reserved CLI values, bibliography sources/styles, declaration content and logo rejection |
| [Terms](../tests/rendered/terms/README.md) | 25 | Abbreviation/glossary first use, repeated terms, native page references, supplied index entries and explicit unsupported-extraction diagnostics |
| [Blind review](../tests/rendered/cor04/README.md) | 10 | Structured identity projection, identified controls and visible/native residual-identity failures |
| [Native image inputs](native-images.md) | 20 | PNG pixels, original JPEG encoding/bytes, SVG vectors, native paths, byte inputs and alternative text under four profiles |
| [Layout and order](layout-order.md) | 9 | Bibliography order/title, Roman/Arabic pagination, duplex behavior, native destinations and controlled A4/30 mm geometry |
| [Optional sections](optional-sections.md) | 47 | Typed funding, prior work, assistance and creative records; publication cardinality; independent front-matter order; private AI-note rejection |

These corpora supplement the 14 COR-01 and three COR-02 cases for 162 regression
cases. The terms corpus contains 17 validated PDFs and eight required diagnostic
rejections. The configuration corpus contains 23 validated PDFs and eleven
required diagnostic rejections. Blind-review assertions deliberately retain
three authored-residual PDFs whose identity scans **fail**; they are evidence
that residual identifiers are detected, not reviewer-ready output. The optional
section corpus adds 21 validated PDFs and 26 required diagnostic rejections,
including one deliberately failed authored-identity scan and one clean blind
control. An expected privacy failure is retained as a failure in its native
report even when the surrounding regression assertion passes.

The same canonical result also includes two bounded follow-up corpora:

| Corpus | Cases | Checked behavior |
| --- | ---: | --- |
| [Typst contract adapter](typst-contract-adapter.md) | 21 | Five-layer normalization and the supported metadata/order slice: seven PDF outputs, nine required validation rejections and five explicit unsupported outcomes |
| [Native evidence](native-evidence.md) | 16 | Fixed-expression semantic extraction and source/output-bound dependency inventories: six accepted evidence results and ten required native or schema rejections |

Together with the 162 rendering cases, these define 199 bounded regression
cases. The adapter uses a separate
entry point and native report; canonical compatibility registration and full
CON-02/CON-03 acceptance remain planned or blocked. Its unsupported outcomes are
not rendered passes. The native validator preserves valid optional false/null/
empty values but rejects missing or malformed required evidence. Successful
COR-04/COR-05 dependency captures now bind the actual compile, source, output and
native report bytes before retaining a normalized inventory.

The six-helper Python coverage scope adds the bounded adapter producer and
native evidence validator to the four existing helpers. The adapter corpus
runner, native orchestration and fixture/PDF oracles are measured through their
actual canonical execution, not included in that line/branch denominator.
The existing 80% floors are unchanged; see [maintenance](maintenance.md).
The complete composed source still requires fresh canonical and hosted results;
historical focused runs do not qualify reconstructed support files or later
review corrections.

These checks do not complete the shared five-layer adapter contract, all
conditional submission policy, arbitrary-content anonymity, PDF/UA or PDF/A,
or genuine human accessibility evaluation. Their source and receiving revision
still need the applicable hosted results before a release claim.

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

Review the checks for the exact PR head before integration.

Hosted qualification snapshot, 15 November 2026 (Australia/Brisbane):
final PR #10 head `0f2f2ecc4b4a0ba3e99a1bb2f84bf5cec5ee5068` passed
[Quality gates](https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43608082998)
(full verification, workflow lint, dependency review and all four profiles),
[Privacy and secrets](https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43608082658)
and [CodeQL Python/Actions](https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43608078096).
The CodeQL result reported no new alerts in changed code. The extended corpus
was intentionally skipped for the ordinary PR event.

PR #10 merged as `b947d5ea0ad1a9c118a9c3670bcb82200052c9a2`; its receiving
[Quality](https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609103472),
[Privacy](https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609103263)
and [CodeQL](https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609102803)
runs also passed. PR-only dependency review and the scheduled/manual extended
corpus were intentionally skipped on the push event. Later commits require their
own applicable results; configuration, historical success and skipped jobs do
not replace execution. The [parent evidence](quality-frontier-evidence.md) and
[integration receipt](maintenance/issue-5-integration-receipt.json) record later
integration. Earlier baseline and local-test observations remain in the
[historical maintenance receipt](maintenance/issue-5-receipt.json).

Separate load testing, distributed-system tests and service deployment lanes
were not warranted for issue #4's original foundation. Typst itself is outside
CodeQL's language coverage.
The property suite is not a proof of all rendering combinations, a full Typst
fuzzer, a scientific-content validator or an accessibility conformance audit.
The normal compile/PDF lane requires the existing package/tool downloads and
is not described as offline security qualification.

The foundation also did not require a separate consumer/provider contract-test
lane for its inspected boundaries. This is a scoped historical decision, not
a repository-wide exclusion. [Issue #14](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/14)
owns the shared UMTHESIS schemas, fixtures and adapter boundary; its acceptance
uses the existing verification orchestration. The
[schema/API milestone](thesis-contract.md) now supplies versioned inputs and
validation. The bounded Typst adapter now has a separate native slice and report;
both canonical document adapters retain their separate execution acceptance.

No Conductor directory exists at the inspected baseline. This document records
the issue's scope, acceptance commands and exclusions without creating a
separate project-management system for that historical increment. The later
[UMTHESIS track](../conductor/tracks/umthesis_v1_20261115/index.md) records the
current document programme.
