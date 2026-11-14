# Quality frontier: evidence and closure for issue #6

This record reconciles [#6][parent] with its two implementation issues,
[#4][testing] and [#5][security]. **The parent remains open.** Neither child was
complete at this snapshot. Update the issue checklist only after the evidence
below has been refreshed against the integrated revision.

Snapshot: 15 November 2026 (Australia/Brisbane).
Inspected main: `6d4652936b4eabaac29462ab8caf86e248c0f96a`.
The [complete source tree][tree] contains three committed workflows, Python
helpers and Typst templates. The original one-workflow audit is historical.
This is a dated acceptance record, not a live settings monitor.

## Acceptance and ownership

"Present" describes source/configuration. "Passed" requires executed evidence at
the stated commit. Missing access, queued jobs and unavailable infrastructure are
blockers or unknowns; they are never applicability exclusions.

| Requirement | Evidence at the inspected revision | Remaining owner/action |
| --- | --- | --- |
| Property-based tests | No property suite in the tree. Python validators and CSV helpers provide meaningful targets; see the reproducer below. | #4: bounded, deterministic cases, replay instructions and failure thresholds. |
| Permissions, concurrency, immutable actions | [CI][ci] and [privacy][privacy] restrict default permissions and cancel superseded runs. Their action/workflow references are immutable. | #4: preserve these controls when adding checks. |
| Compilation and retained PDFs | The [CI caller][ci] selects four profiles. The [pinned reusable workflow][shared] provides formatting, compilation and PDF checks, a 30-minute job limit and 14-day artifacts. | #4: successful execution on the integrated revision; historical runs do not certify it. |
| Workflow lint and dependency review | Neither gate is invoked by the inspected caller or reusable workflow. | #4: implement applicable checks or record a narrow, source-backed exclusion. |
| CodeQL | A [setup run][codeql-run] for Python and Actions is queued on the inspected main. | #4: verify completed analysis; setup presence is not a pass. |
| Secret/privacy scanning | [Run 42786418792][privacy-run] passed on the inspected main. | Preserve the passing baseline and obtain final-revision evidence. |
| Dependency maintenance | [Renovate configuration][renovate] inherits the central preset. [Dashboard #7][dashboard], authored by renovate[bot], lists detected Typst/Actions dependencies and scheduled updates. No Dependabot file is present. | #5: existing bot access/activity is evidenced; preserve update coverage. |
| Solo-maintainer context | [AGENTS.md][agents], [CONTRIBUTING.md][contributing] and [SECURITY.md][policy] exist. Source policy prohibits required reviewers, CODEOWNERS approval and team gates. | #5: complete repository-specific guidance and owner recovery evidence. |
| One-command validation | AGENTS and CONTRIBUTING prescribe `make verify`; the [Makefile][makefile] has no such target. Reproduced exit status: 2. | #4/#5: agree ownership of one working command and run it successfully. |
| Ruleset / stable required checks | The [rulesets collection][rulesets] returned `[]`; the [main branch summary][branch] returned `protected: false` and no required checks. | #5: inventory bots, enforce stable automated checks and prevent force-push/deletion while retaining owner recovery. |
| Issue templates and settings drift receipt | Neither is present in the inspected source tree. | #5: provide templates and a verifiable settings receipt. This parent record does not replace that receipt. |
| Real coverage and Codecov | No coverage suite/uploader in the inspected tree; no Codecov check on the inspected main. | #5 with #4: measure executable Python code, upload with OIDC and verify repository/commit activity. Do not describe Python coverage as Typst layout coverage. |
| Publishing | [Release workflow][release] triggers on version tags, checks package/tag agreement and scopes write permission to the release job. | Preserve tag-only publishing and zero mandatory human approvals. |

The protection-detail API is not available to the auditing integration. That
access denial is an unknown, not evidence that protection is absent; the
readable ruleset collection and branch summary are the separate observations
reported above. Live settings endpoints and the dashboard can change after this
snapshot.

## Executed evidence and limits

| Check | Revision | Observation |
| --- | --- | --- |
| [Privacy and secrets][privacy-run] | `6d4652936b4eabaac29462ab8caf86e248c0f96a` | Passed, push run on 10 November 2026. |
| [Historical Typst matrix][typst-run] | `28bb38fd3b2965b8d102acd97e0abcbf1cd961b6` | Passed on 5 October 2026. This is not a pass for the inspected main. Artifact retention does not imply old PDFs remain downloadable. |
| [CodeQL setup][codeql-run] | `6d4652936b4eabaac29462ab8caf86e248c0f96a` | Queued when inspected; no successful analysis claimed. |
| `make verify` against the inspected Makefile | Makefile blob `b7a7cfde434018194c496413cc977ebaa301d81d` | Failed: `No rule to make target 'verify'`, exit 2. Compilation was not reached. |
| Python validator probe below | manage_terms.py blob `9e3f9932466090bfd8556148de3369b4ea8a905c` | Valid entries returned no errors. Mixed valid/non-dictionary entries raised `AttributeError` in both orders for both validators. This is failing baseline evidence. |

The local probes used exact file snapshots retrieved from GitHub, not a complete
checkout. They neither establish a full build pass nor validate rendered PDFs.

### Reproduce the validator failure

Run this read-only probe from a checkout of the inspected revision:

```bash
python3 -B - <<'PY'
import importlib.util

spec = importlib.util.spec_from_file_location(
    "manage_terms", "scripts/manage_terms.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cases = (
    ("validate_abbreviations",
     {"key": "Artificial Intelligence", "short": "AI",
      "long": "Artificial intelligence"}),
    ("validate_glossary",
     {"term": "Thesis", "definition": "Research thesis"}),
)
for name, valid in cases:
    validate = getattr(module, name)
    print(name, "valid:", validate([valid]))
    for entries in ([None, valid], [valid, None]):
        try:
            print(name, validate(entries))
        except AttributeError as error:
            print(name, type(error).__name__, str(error))
PY
```

The diagnostic catches exceptions to report all four failures; its process exit
status is not a passing test result. The nested duplicate-check loops call
`other.get(...)` before establishing that every peer is a dictionary. #4 should
retain regression cases alongside generated malformed-input cases. Do not
replace that lane with a second testing framework.

## Pending implementation: PR #10

The testing lane has opened [PR #10][testing-pr] at
`4b6107b7b024305c609885037ee049612bb54d75`. Its source fixes the mixed-entry
crash, uses TOML parsing for package metadata, adds the canonical verification
command, and adds properties, workflow lint and dependency review. It remains
unmerged; the main-only gaps above must not be read as a request to duplicate
those changes.

Independent execution used exact GitHub file snapshots, verified against their
Git blob SHAs, on **Python 3.12.14**. The actual CLI and JSON report generation
were exercised:

| Invocation (seed 20261115) | Executed result |
| --- | --- |
| `python3 -B tests/test_properties.py --seed 20261115 --cases 64 --report build/property-tests.json` | 10 tests; 640 generated iterations; 0 failures/errors/skips; report `passed: true`. |
| `python3 -B tests/test_properties.py --seed 20261115 --cases 512 --report build/property-tests-deep.json` | 10 tests; 5,120 generated iterations; 0 failures/errors/skips; report `passed: true`. |

Both reports identify these exact source SHA-256 hashes:

| Source | SHA-256 |
| --- | --- |
| `scripts/manage_terms.py` | `19a131f7a9ad4dca484a464f19fd9d0eef010d143b0a85eb8c4970f29fc2981b` |
| `scripts/validate_template.py` | `2cb7caa07e791feacc775d228ef7370ec860115fe9d1b9525e0f2498f5885a98` |
| `tests/test_properties.py` | `7aec3fd8231eca047f14a99fde81e6d413bfcf51f7606b5b8ad989d9fd71381e` |

The [verification comment][testing-evidence] records these results. They do not
qualify hosted Python 3.15.1 or PDF compilation. Invoking the new
`scripts/verify.py` failed closed with `Required executable not found: typst`
(exit 1) in this environment.

At inspection, [quality checks][quality-run] and [privacy checks][pr-privacy-run]
were queued for this PR head; the extended corpus is intentionally skipped on
ordinary PRs. No four-profile Typst or CodeQL run was found for that exact head.
Missing and pending runs are not passing evidence. Integration and final-main
verification remain open.

## Applicability decisions

These decisions retain the original audit's narrow scope and should be revisited
when the implementation changes.

| Technique | Decision | Evidence and boundary |
| --- | --- | --- |
| Property-based testing | Warranted; incomplete. | The [Python helpers][terms] validate structured data and transform CSV. Mixed-entry rejection, duplicate handling and normalized round trips have concrete, bounded invariants. Tests must state the supported input domain and normalization rules. |
| Mutation testing | Exclude a dedicated mutation lane for this increment. | The first useful gap is an executable regression/property suite for the small helper surface. A mutation service, score gate and equivalent-mutant maintenance are not proportionate evidence for this template now. Reassess after the baseline suite exists or logic grows. |
| Deterministic simulation testing (DST) | Not applicable to the inspected application. | The repository builds documents and runs local helpers; it contains no distributed service, replicated state machine or simulated event scheduler requiring a separate fault-simulation harness. |
| Metamorphic testing (MT) | No separate mandatory lane. | Normalized round trips and input permutations can be expressed within the property suite. This excludes a duplicate framework/job, not useful metamorphic assertions. |
| Consumer/provider contract testing | No separate mandatory framework. | The source exposes Typst macros and local helper commands, not an independently deployed producer/consumer protocol. Compile examples and helper input/output tests remain necessary. Revisit if an external service or versioned interchange contract is introduced. |

These exclusions do not waive Python analysis, meaningful coverage, compilation,
workflow security, or an applicable dependency gate. An unsupported ecosystem
would justify only the unsupported portion of a check, with evidence.

## Closure procedure

1. Re-read #4 and #5 and the current main commit. For each acceptance item, link
   the implementation and an executed result, or document its specific
   applicability exclusion. An issue state or checked box alone is insufficient.
2. Reconcile the child changes on main and run the canonical verification command
   and applicable hosted checks. Record the PR head tested, integrated main SHA,
   commands/tool versions, conclusions and workflow URLs. Distinguish PR checks
   from checks on the integrated revision.
3. Confirm the live ruleset, stable required checks, bot operation and owner
   recovery without mandatory human approvals. Verify Codecov activity and its
   actual coverage scope. Keep missing authorization or external activation
   explicitly open.
4. Refresh this record or link the replacement receipt in #6, then complete both
   child checkboxes and close the parent only when every requirement is satisfied
   or has an evidence-backed exclusion.

[Offline security PR #9][offline-pr] is a separate conditional rollout. Its
[offline run][offline-run] was queued at this snapshot; its body requires
isolated-runner/image/local-model provisioning and real integration validation.
A passing privacy check does not qualify that integration. Preserve its gate;
do not provision it here or add it as a third dependency of #6.

[parent]: https://github.com/edithatogo/unimelb-thesis-template-typst/issues/6
[testing]: https://github.com/edithatogo/unimelb-thesis-template-typst/issues/4
[security]: https://github.com/edithatogo/unimelb-thesis-template-typst/issues/5
[tree]: https://github.com/edithatogo/unimelb-thesis-template-typst/tree/6d4652936b4eabaac29462ab8caf86e248c0f96a
[ci]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/.github/workflows/ci-cd.yml
[privacy]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/.github/workflows/privacy-secrets.yml
[shared]: https://github.com/edithatogo/repository-standards/blob/f37a6c6a9764766ac25d2c65c7ec71f3a7a9fd87/.github/workflows/typst-ci.yml
[privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/42786418792
[typst-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/37292010225
[codeql-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43604503605
[renovate]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/renovate.json
[dashboard]: https://github.com/edithatogo/unimelb-thesis-template-typst/issues/7
[agents]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/AGENTS.md
[contributing]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/CONTRIBUTING.md
[policy]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/SECURITY.md
[makefile]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/Makefile
[terms]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/scripts/manage_terms.py
[rulesets]: https://api.github.com/repos/edithatogo/unimelb-thesis-template-typst/rulesets
[branch]: https://api.github.com/repos/edithatogo/unimelb-thesis-template-typst/branches/main
[release]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/6d4652936b4eabaac29462ab8caf86e248c0f96a/.github/workflows/release.yml
[offline-pr]: https://github.com/edithatogo/unimelb-thesis-template-typst/pull/9
[offline-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43003338960
[testing-pr]: https://github.com/edithatogo/unimelb-thesis-template-typst/pull/10
[testing-evidence]: https://github.com/edithatogo/unimelb-thesis-template-typst/pull/10#issuecomment-6878924654
[quality-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43605193230
[pr-privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43605193200
