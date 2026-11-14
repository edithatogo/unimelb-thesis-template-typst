# Quality frontier: evidence and closure for issue #6

This record reconciles [#6][parent] with its two implementation issues,
[#4][testing] and [#5][security]. Final closure is recorded on those issues
after this evidence commit and its receiving revision are qualified. Candidate
checks, historical baseline evidence and receiving-main acceptance are recorded
separately. Update the issue checklist only after the implementation and
applicable checks have been verified on the integrated revision.

Refreshed: 15 November 2026 (Australia/Brisbane).
Historical baseline main: `6d4652936b4eabaac29462ab8caf86e248c0f96a`.
The [baseline source tree][tree] contains three committed workflows, Python
helpers and Typst templates. The original one-workflow audit is historical.
This is a dated acceptance record, not a live settings monitor.

## Latest foundation and integration status

Final integration observation: **2026-11-14T21:31:11Z** (15 November 2026,
Brisbane). The parallel [citation metadata PR #26](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/26)
added only `CITATION.cff` to main `7d7e6a713486cd83cc06cbbac0c1a967a1c87f07`.
This update incorporates that commit and preserves the citation blob unchanged;
the implementation and workflow blobs still match qualified main `9375798`.

| Scope | Latest recorded evidence | Outstanding acceptance |
| --- | --- | --- |
| #4 / PR #10 | Merged as `b947d5ea0ad1a9c118a9c3670bcb82200052c9a2`; #4 is closed. The receiving-main [quality][receiving-quality-run], [privacy][receiving-privacy-run] and [CodeQL][receiving-codeql-run] workflows all succeeded. | The #4 foundation is integrated and qualified at this revision. Preserve these checks after #12 and the final evidence updates. |
| #5 / PR #12 | Qualified source `7e2d09c934c3c9805a222f39c6fd073885196b48` merged as `937579897af22d7d28f20a49e94a1bdbe4e05855`. Source and receiving workflows, coverage uploads and Codecov results passed. Source patch coverage is 98.91%; combined three-tool coverage is 97.74%. Canonical verification passed 61 unit tests, 640 property iterations and real PDF checks. | Implementation and receiving main are qualified at these revisions. Qualify this final documentation head and its receiving revision separately. |
| Live protection | [Ruleset 27266891][live-ruleset] is active with eight Actions contexts, required conversation resolution, zero required approvals and owner-only recovery. The [full inventory][qualified-rulesets] returned **MATCH / exit 0**, observed at `2026-11-14T15:51:12Z`. | Retain the qualified snapshot and its provenance; confirm freshness before final closure. The earlier two mismatches have been corrected. |
| Receiving main | #12 receiving SHA `937579897af22d7d28f20a49e94a1bdbe4e05855` passed all five workflows and received successful Codecov legacy status `58926800850` from `codecov[bot]`. Its independently measured coverage and exact producer metadata are recorded below. | The earlier queued observation is superseded by actual execution. Subsequent citation metadata in main `7d7e6a7` is preserved by this evidence update. |
| Central classification | [Central PR #142][central-classification-pr] merged as `e195af3b0f46db74e797c5bf2e177b7882085186` after all applicable checks passed on `a54fc107`. Receiving tree `db2e61f6` equals the tested tree. The registry records qualified receiving-main coverage and published-artifact applicability. | The classification dependency is integrated. Broader collector/release controls retain their separate owners. |

## Historical baseline acceptance and ownership

"Present" describes source/configuration. "Passed" requires executed evidence at
the stated commit. Missing access, queued jobs and unavailable infrastructure are
blockers or unknowns; they are never applicability exclusions.
The table below preserves the gaps at baseline `6d4652936b4eabaac29462ab8caf86e248c0f96a`.
The integrated #4 implementation and later #5 work are reconciled in their own
sections; these historical gaps do not describe current main.

| Requirement | Evidence at the inspected revision | Original owner / acceptance |
| --- | --- | --- |
| Property-based tests | No property suite in the tree. Python validators and CSV helpers provide meaningful targets; see the reproducer below. | #4: bounded, deterministic cases, replay instructions and failure thresholds. |
| Permissions, concurrency, immutable actions | [CI][ci] and [privacy][privacy] restrict default permissions and cancel superseded runs. Their action/workflow references are immutable. | #4: preserve these controls when adding checks. |
| Compilation and retained PDFs | The [CI caller][ci] selects four profiles. The [pinned reusable workflow][shared] provides formatting, compilation and PDF checks, a 30-minute job limit and 14-day artifacts. | #4: successful execution on the integrated revision; historical runs do not certify it. |
| Workflow lint and dependency review | Neither gate is invoked by the inspected caller or reusable workflow. | #4: implement applicable checks or record a narrow, source-backed exclusion. |
| CodeQL | The [baseline default-setup run][codeql-run] completed successfully, including the Python and Actions analysis jobs. | #4: obtain candidate and receiving-revision analysis; a successful baseline run does not certify later code. |
| Secret/privacy scanning | [Run 42786418792][privacy-run] passed on the inspected main. | Preserve the passing baseline and obtain final-revision evidence. |
| Dependency maintenance | [Renovate configuration][renovate] inherits the central preset. [Dashboard #7][dashboard], authored by renovate[bot], lists detected Typst/Actions dependencies and scheduled updates. No Dependabot file is present. | #5: existing bot access/activity is evidenced; preserve update coverage. |
| Solo-maintainer context | [AGENTS.md][agents], [CONTRIBUTING.md][contributing] and [SECURITY.md][policy] exist. Source policy prohibits required reviewers, CODEOWNERS approval and team gates. | #5: complete repository-specific guidance and owner recovery evidence. |
| One-command validation | AGENTS and CONTRIBUTING prescribe `make verify`; the [Makefile][makefile] has no such target. Reproduced exit status: 2. | #4/#5: agree ownership of one working command and run it successfully. |
| Ruleset / stable required checks | The [rulesets collection][rulesets] returned `[]`; the [main branch summary][branch] returned `protected: false` and no required checks. | #5: inventory bots, enforce stable automated checks and prevent force-push/deletion while retaining owner recovery. |
| Issue templates and settings drift receipt | Neither is present in the inspected source tree. | #5: provide templates and a verifiable settings receipt. This parent record does not replace that receipt. |
| Real coverage and Codecov | No coverage suite/uploader in the inspected tree; no Codecov check on the inspected main. | #5 with #4: measure executable Python code, upload with OIDC and verify repository/commit activity. Do not describe Python coverage as Typst layout coverage. |
| Publishing | [Release workflow][release] triggers on version tags, checks package/tag agreement and scopes write permission to the release job. | Preserve tag-only publishing and zero mandatory human approvals. |

The baseline protection-detail API denial was an unknown, not evidence that
protection was absent. The readable empty ruleset collection and unprotected
branch summary were separate baseline observations. Later settings access and
initial drift and the subsequent verified match are recorded below. Live endpoints and the
dependency dashboard can change after a snapshot.

## Executed evidence and limits

| Check | Revision | Observation |
| --- | --- | --- |
| [Privacy and secrets][privacy-run] | `6d4652936b4eabaac29462ab8caf86e248c0f96a` | Passed, push run on 10 November 2026. |
| [Historical Typst matrix][typst-run] | `28bb38fd3b2965b8d102acd97e0abcbf1cd961b6` | Passed on 5 October 2026. This is not a pass for the inspected main. Artifact retention does not imply old PDFs remain downloadable. |
| [CodeQL default setup][codeql-run] | `6d4652936b4eabaac29462ab8caf86e248c0f96a` | Subsequently completed successfully: both `Analyze (python)` and `Analyze (actions)` ran their CodeQL analysis steps. This qualifies the baseline only. |
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

## PR #10: integrated and qualified on main

The testing lane's [PR #10][testing-pr] was merged as
`b947d5ea0ad1a9c118a9c3670bcb82200052c9a2`. Its qualified PR head was
`0f2f2ecc4b4a0ba3e99a1bb2f84bf5cec5ee5068`; both commits have source tree
`24f3dfbafd35c239bca8a43c77cf1b4aadb738cc`. The change fixes the mixed-entry
crash, uses TOML parsing for package metadata, supplies the canonical
verification command, and adds properties, workflow lint and dependency review.
Issue #4 is closed. Its historical main-only gaps above are resolved by this
integrated implementation.

The first independent helper execution below used the earlier candidate
`4b6107b7b024305c609885037ee049612bb54d75`.

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

These cases exercise helper contracts and manifest parsing. The CSV domain
accounts for outer-whitespace normalization and the related-term delimiter.
The term-management CLI still uses sample data in its Typst-input path; these
properties do not certify a general Typst data parser.

The [verification comment][testing-evidence] records these results. That
specific helper execution did not qualify hosted Python 3.15.1 or PDF
compilation: the auditor's initial `scripts/verify.py` invocation failed closed
with `Required executable not found: typst` (exit 1). This is an earlier
environment limitation, not the result of the later complete build execution.

At that earlier inspection, [quality checks][quality-run] and
[privacy checks][pr-privacy-run] were queued and no four-profile Typst or CodeQL
run was found. Those observations are historical.

The later head `c60bebd294fe2991ae2d29f15f0a87ee80aad153` moves the preserved
four-profile matrix into `quality.yml`. All three tested Python blobs are
unchanged. Its [quality run][current-quality-run] completed successfully with
all four profile jobs, verification, lint and dependency review; its
[privacy run][current-privacy-run] also succeeded. The extended corpus is
intentionally skipped on ordinary PRs.

The PR author separately records complete local `make verify` passes on
Python 3.15.1 and 3.12.14, both property corpus sizes, and real Typst 0.15.1/PDF
checks. The four thesis profiles produced 55, 55, 54 and 63 pages respectively;
the sample produced 7 pages. Local font fallback and unchanged-example parsing
warnings are disclosed in the [candidate validation record][testing-record].
These full-build results are distinct from the original helper-only audit.

The final PR head `0f2f2ecc4b4a0ba3e99a1bb2f84bf5cec5ee5068` adds the dated
validation record. Its [quality][latest-quality-run],
[privacy][latest-privacy-run] and [CodeQL][latest-codeql-run] workflows passed
before integration. The following distinct runs qualify the actual receiving
main revision `b947d5ea0ad1a9c118a9c3670bcb82200052c9a2`; all had succeeded by
14 November 2026, 15:33:46 UTC:

| Receiving-main workflow | Run | Result |
| --- | --- | --- |
| Quality gates | [43609103472][receiving-quality-run] | Success, including all four profile builds and applicable source/workflow gates. |
| Privacy and secrets | [43609103263][receiving-privacy-run] | Success. |
| CodeQL default setup | [43609102803][receiving-codeql-run] | Success. |

The identical source tree explains which implementation was integrated; the
post-merge runs establish the separate receiving-revision execution evidence.

## PR #12: source and receiving main qualified

The security/maintainer lane's [PR #12][security-pr] was merged into **main** as
`937579897af22d7d28f20a49e94a1bdbe4e05855` after qualifying source head
`7e2d09c934c3c9805a222f39c6fd073885196b48`. Both have tree
`dad36e87cc3971538228056a04c091e59023ab98`. The preserved
merge `04478c830d29c04081816deea7bbda47891871a6` incorporates #10's receiving
revision `b947d5ea0ad1a9c118a9c3670bcb82200052c9a2`.
It reuses the integrated verification command and adds
issue forms, updated contributor/security context, desired-ruleset validation,
a drift checker, maintenance tests, and a pinned Codecov OIDC upload job.
Its source head and receiving main, including provider acceptance, are
qualified at their exact recorded commits. Final documentation qualification
remains separate.

### Historical PR #12 candidate

The [earlier receipt][security-prior-receipt] records **54 passing local unit
tests** on Python 3.12.14 and **97.59% combined line/branch coverage**, with an
80% floor. The later receipt also records the subsequent 54-test hosted run
on Python 3.15.1 at `66beec5`. These are the implementer's recorded results,
not a second execution by this audit. Coverage is explicitly limited to
`scripts/preflight.py`, `scripts/validate_template.py` and
`scripts/check_repository_policy.py`; it does not measure the whole repository
or Typst rendering.

The [historical quality][security-quality-run], [maintenance][security-maintenance-run]
and [privacy][security-privacy-run] workflows all succeeded on `66beec5`.
The actual [Codecov check][codecov-checks] named `codecov/patch` completed with
`success` under app ID 254 and reported **98.80% of the diff hit** against an
80% target; [Codecov's PR view][codecov-pr] identifies the repository and PR.
This verifies service activity and the check on that candidate. It does not
turn 97.59% combined helper coverage into whole-repository coverage, and it
does not qualify uncommitted changes or a future receiving revision.

### Earlier policy-checker follow-up

The policy-checker inventory fixes were published at `b1b465c`. Malformed secondary
ruleset classification returns UNKNOWN (exit 2), and additional active push
rulesets return DRIFT (exit 1); neither can silently pass as MATCH. Five
regression test methods cover the follow-up.

The [policy-fix receipt][security-receipt] records a local canonical `make verify`
pass on Python 3.15.1: **59 unit tests**, 10 properties / 640 generated
iterations, and actual thesis/sample PDF checks (55 and 7 pages).
Coverage.py 7.17.3 measured **97.72329246935202% combined line/branch coverage**:
372/381 lines, 186/190 branches and zero excluded lines, within the same
three-file scope and above the 80% floor. The receipt records the exact source
SHA-256 hashes, including the changed policy checker. These are local
execution results for the published source, not a claim of hosted completion.

### Qualified source: governance correction and local execution

The current `7e2d09c` source preserves the two inventory fixes and also requires
the pull-request rule and explicit conversation resolution. Two further
regression methods bring the maintenance suite to **61 unit tests**. The
[checked-in policy][current-desired-policy] retains zero mandatory human
approvals and owner recovery.

The integrator executed full `make verify` on this exact head with **Python
3.15.1**: 61 unit tests, **10 properties / 640 generated iterations** with seed
`20261115`, source/package/policy validation, and real thesis/sample PDF checks
(55 and 7 pages). Typst was 0.15.1 and qpdf was 12.4.2; extracted text was
nonempty. The current [PR description][security-pr] records this run. Local
`build/verification/report.json` and `build/property-tests.json` retain the
successful results; this document does not substitute them for hosted evidence.

Coverage.py **7.17.3** passed the same three-file component's 80% floor with
**97.73913043478261% combined line/branch coverage**: **374/383 statements**,
**188/192 branches**, and **zero excluded lines**. The separate statement and
branch percentages are approximately 97.65% and 97.92%; the combined number is
not a line-only percentage. The retained native report is `build/coverage.json`.

| Coverage source at `7e2d09c` | SHA-256 |
| --- | --- |
| `scripts/preflight.py` | `6c98b519178a46eacc99d6fc70d00fe8e2324631072cc40d1435875a7ce635b6` |
| `scripts/validate_template.py` | `2cb7caa07e791feacc775d228ef7370ec860115fe9d1b9525e0f2498f5885a98` |
| `scripts/check_repository_policy.py` | `36707d2ad9ca2a6ed0931549c878d04a960597018a1ed75a7e93b0f5781c7ad1` |

At the 14 November 2026, **15:52:18 UTC** read, current-head
[quality][security-current-quality-run], [privacy][security-current-privacy-run]
and [CodeQL][security-current-codeql-run] workflows had succeeded. The
[Python validation coverage job][current-coverage-job], ID `132491525752`,
also succeeded. Its logs record Python 3.15.1, **61 tests**, coverage.py 7.17.3
and **97.74%** scoped combined coverage. It retained maintenance-evidence
artifact `14120206858`; the refreshed receipt records its digest.

The [Maintenance workflow][security-current-maintenance-run] subsequently
completed successfully, including the actual OIDC upload step in
[coverage-upload job 132495689999][current-upload-job]. The
[source-head check inventory][current-checks] now includes
[Codecov check 132503365652][current-codecov-check], owned by app **254**, with
`success` on the exact `7e2d09c` SHA at `2026-11-14T16:03:15Z`. It reports
**98.91% of the diff hit** against an 80% target. This patch percentage is
separate from 97.74% combined helper coverage. Source-head provider acceptance
is complete. Earlier 54-test/97.59% evidence remains scoped to `66beec5` and
the 59-test/97.72% result to `b1b465c`; no result is transferred to receiving main.

The [current integration receipt][qualified-receipt] preserves the baseline
empty-ruleset observation and the earlier 59-test source/coverage evidence with
their original revision attribution. It separately records current local and
hosted results, live MATCH, successful source Codecov processing and the actual
PR #12 receiving SHA with its completed workflow and provider results. The
[historical maintenance receipt][historical-maintenance-receipt] remains
unchanged; the separate integration receipt preserves that earlier record.

### Live policy: active and matched

[Ruleset 27266891][live-ruleset] is active on the default branch. The qualified
full inventory contains all **eight** required status contexts bound to GitHub
Actions app ID **15368**, `required_review_thread_resolution: true`, zero
required approvals, and owner User **15080672** as the only bypass actor with
`always` recovery. It blocks branch deletion and non-fast-forward updates.

The [qualified inventory][qualified-rulesets] was observed at
**`2026-11-14T15:51:12Z`** and has SHA-256
`e000963b1a67731ed577595d8891d1d14be1ad3e267ed251162a660e7357a4a1`.
The current `7e2d09c` policy checker returns **MATCH / exit 0** for this complete
inventory; an independent local replay confirmed that result. The preceding
seven-check snapshot correctly returned DRIFT before conversation resolution
and the coverage context were corrected. The earlier empty baseline is retained
as a different observation. MATCH certifies the supplied inventory; its
observation time and source remain part of the evidence.

Other security settings retain the
[existing authenticated inspection record][security-settings-record]: private vulnerability reporting, Dependabot
alerts, secret push protection and Dependabot security updates were reported
enabled. A later independent follow-up could not obtain a usable native browser
window, repository metadata omitted `security_and_analysis`, and classic
branch-protection detail access returned HTTP 403. These extra settings were
not independently reverified in this refresh. The live-ruleset readback above
is separate evidence.

The actual receiving revision is `937579897af22d7d28f20a49e94a1bdbe4e05855`.
The following exact-revision workflows completed successfully. This supersedes
the historical queued observation at 14 November 2026, 16:26 UTC:

| Receiving-main workflow | Run | Recorded result |
| --- | --- | --- |
| Quality gates | [43613548339][security-receiving-quality-run] | Success; all four profiles, workflow lint and canonical verification. |
| Maintenance | [43613547923][security-receiving-maintenance-run] | Success; 61 tests, measured coverage and OIDC upload. |
| Privacy and secrets | [43613547805][security-receiving-privacy-run] | Success. |
| CodeQL default setup | [43613547696][security-receiving-codeql-run] | Success for Python and Actions. |
| Dependency graph update | [43613554074][security-receiving-graph-run] | Success. |

The receiving [coverage job][receiving-coverage-job] independently ran **61 tests**
on Python 3.15.1 with coverage.py 7.17.3. Its report reproduced **97.74% combined
coverage**: 374/383 statements and 188/192 branches, zero excluded lines.
The test count is evidenced by the job log; the artifact retains the XML/JSON
coverage reports. GitHub metadata identifies artifact **14121984203**, digest
`sha256:091be1f0f40822bf1c990b772a831417050ad9ac943a893f0ed653557243a0a3`,
and template-verification artifact **14122449066**, digest
`sha256:1a175ec43896894a6c57a1e90c1d5d5dc8ba5cdc278bdcffbebe9f854a549cae`.
Those archive digests were read from GitHub metadata, not independently
recomputed in this refresh. Dependency review and the extended corpus are
expected main-push exclusions, recorded as skips.

The [receiving OIDC upload][receiving-upload-job] completed successfully at
`2026-11-14T17:10:14Z`. The [commit-status objects][receiving-statuses] then
recorded **codecov/patch: success**, status **58926800850**, at
`2026-11-14T17:10:25Z`, from **codecov[bot]**, user ID **22429695**. Its
[exact-commit report][receiving-codecov] reports unchanged coverage when comparing
`7e2d09c...9375798`. This is a legacy commit status, not a check-run; no check
ID or inferred app identity is assigned to it. It does not remeasure the source
PR's 98.91% patch coverage.

The prior evidence head `1df319593c1df31d2a7314fbb309d23a8391d86f` also passed
all applicable checks and Codecov check **132524110046** from app **254**.
This refreshed documentation head and its receiving main require their own
applicable checks. Their final execution and closure evidence are recorded on
PR #11 and issues #5/#6 after publication; the versioned receipt remains a dated
observation rather than attempting to contain its own future commit identity.

## Central classification and programme ownership

[Central PR #142][central-classification-pr], owned by
[central typesetting #5][central-typesetting], is merged as
`e195af3b0f46db74e797c5bf2e177b7882085186` at `2026-11-14T21:30:48Z`.
The repository permits squash merges. Its qualified head was
`a54fc10734f8c84396019e3a39c98241dae3df40`; the actual receiving tree is
`db2e61f61672ced4a8bd45324415f661b89e85de`, identical to the tested tree.
All applicable final-head policy, privacy, security-lint and Python/Actions
CodeQL checks passed. All five registered push checks also succeeded on
receiving commit `e195af3`; their identities are retained in the integration
receipt. Estate collection/publication were expected PR-event skips, not
executed estate conformance.

The central correction changes only this consumer's registry row and its
component assessment. It retains the `typesetting-template` archetype and
`typst` profile, marks executable-helper coverage warranted, and binds Codecov
evidence to qualified receiving main
`937579897af22d7d28f20a49e94a1bdbe4e05855`, with receiving qualification
true. The [central merge][central-classification-merge] and full tree were
read back before recording integration. Separate genomics and LaTeX changes
in PRs #119/#141 retain their existing ownership; this merge preserved their
registry entries.
The classification also makes published-artifact supply-chain applicability
explicit: source releases exist and the [tag-only workflow][current-release]
is configured to publish a compiled PDF. This does not establish executed
artifact-bound attestations or new collector enforcement. The separate
assessment records those limits and the existing release/evidence owners.
The foundation requires truthful component applicability and evidence; later
document-production outputs remain with their own implementation issues.

[Programme #13][document-programme] and its #14–25 implementation issues are
separate under GOV-04. The historical #6 child scope remains **#4 and #5**.
The broader document programme does not add new children or completion
requirements to this foundation record.

## Applicability decisions

These decisions retain the original audit's narrow scope and should be revisited
when the implementation changes.

| Technique | Decision | Evidence and boundary |
| --- | --- | --- |
| Property-based testing | Warranted; implemented, executed and integrated through #10. | The [Python helpers][terms] validate structured data and transform CSV. Mixed-entry rejection, duplicate handling and normalized round trips have concrete, bounded invariants. Tests state the supported input domain and normalization rules. |
| Mutation testing | Exclude a dedicated mutation lane for this increment. | The small helper surface has concrete input/output oracles covered by the regression/property increment. A separate mutation service, score gate and equivalent-mutant maintenance are not proportionate to this template's current scope. Reassess if validation logic grows or review finds that the ordinary suite misses meaningful faults. |
| Deterministic simulation testing (DST) | Not applicable to the inspected application. | The repository builds documents and runs local helpers; it contains no distributed service, replicated state machine or simulated event scheduler requiring a separate fault-simulation harness. |
| Metamorphic testing (MT) | No separate mandatory lane. | Normalized round trips and input permutations can be expressed within the property suite. This excludes a duplicate framework/job, not useful metamorphic assertions. |
| Consumer/provider contract testing | No separate mandatory framework for this foundation; not global non-applicability. | Compile examples and helper input/output tests remain necessary. [Issue #14][document-contract] owns reassessment and the versioned schema, shared-fixture and adapter-conformance tests required by #13. This foundation decision does not exclude that programme's contract testing. |

These exclusions do not waive Python analysis, meaningful coverage, compilation,
workflow security, or an applicable dependency gate. An unsupported ecosystem
would justify only the unsupported portion of a check, with evidence.

## Closure procedure

1. Retain #4's completed implementation and receiving-main evidence. Re-read #5
   and current main, and link each remaining acceptance item to an executed
   result or specific applicability exclusion. Issue state alone is insufficient.
2. Retain #12's completed source and receiving-main qualification, including
   the exact Codecov producer/status identities and measured component scope.
   Qualify the final evidence PR and its actual receiving revision separately.
3. Confirm the live ruleset, stable required checks, bot operation and owner
   recovery without mandatory human approvals. Verify Codecov activity and its
   actual coverage scope. Keep missing authorization or external activation
   explicitly open.
4. Retain the completed central PR #142 integration and qualify this final
   evidence PR and its receiving revision. Record their exact results on PR #11
   and issues #5/#6 after publication. Complete #5's checklist only when those
   gates pass; the parent may close once its original children are satisfied.
   The dated receipt remains immutable evidence of its observation, while
   issue closure records the later integration event. Keep #13–25 under their
   existing owners.

[Offline security PR #9][offline-pr] is a separate conditional rollout. Its
[earlier offline run][offline-run] was queued when inspected; its body requires
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
[current-quality-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43605767014
[current-privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43605766686
[security-pr]: https://github.com/edithatogo/unimelb-thesis-template-typst/pull/12
[security-prior-receipt]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/66beec5cd7b78a9cdc1aad37dd288350184ef14d/docs/maintenance/issue-5-receipt.json
[security-receipt]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/b1b465c74324f75c815cf199ef45d7ff631d20d5/docs/maintenance/issue-5-receipt.json
[testing-record]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/0f2f2ecc4b4a0ba3e99a1bb2f84bf5cec5ee5068/docs/quality-gates.md
[latest-quality-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43608082998
[latest-privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43608082658
[latest-codeql-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43608078096
[security-quality-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43606355918
[security-maintenance-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43606355606
[security-privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43606355629
[codecov-checks]: https://api.github.com/repos/edithatogo/unimelb-thesis-template-typst/commits/66beec5cd7b78a9cdc1aad37dd288350184ef14d/check-runs?per_page=100
[codecov-pr]: https://app.codecov.io/gh/edithatogo/unimelb-thesis-template-typst/pull/12
[security-current-quality-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609602381
[security-current-maintenance-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609602102
[security-current-privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609602093
[security-current-codeql-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609599167
[receiving-quality-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609103472
[receiving-privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609103263
[receiving-codeql-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609102803
[live-ruleset]: https://github.com/edithatogo/unimelb-thesis-template-typst/rules/27266891
[current-desired-policy]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/7e2d09c934c3c9805a222f39c6fd073885196b48/.github/rulesets/solo-maintainer.json
[current-release]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/7e2d09c934c3c9805a222f39c6fd073885196b48/.github/workflows/release.yml
[central-typesetting]: https://github.com/edithatogo/repository-standards/issues/5
[document-programme]: https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13
[current-coverage-job]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609602102/job/132491525752
[current-upload-job]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43609602102/job/132495689999
[current-checks]: https://api.github.com/repos/edithatogo/unimelb-thesis-template-typst/commits/7e2d09c934c3c9805a222f39c6fd073885196b48/check-runs?per_page=100
[qualified-rulesets]: maintenance/issue-5-qualified-rulesets.json
[qualified-receipt]: maintenance/issue-5-integration-receipt.json
[security-settings-record]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/7e2d09c934c3c9805a222f39c6fd073885196b48/docs/maintenance.md
[central-classification-pr]: https://github.com/edithatogo/repository-standards/pull/142
[historical-maintenance-receipt]: https://github.com/edithatogo/unimelb-thesis-template-typst/blob/7e2d09c934c3c9805a222f39c6fd073885196b48/docs/maintenance/issue-5-receipt.json
[current-codecov-check]: https://github.com/edithatogo/unimelb-thesis-template-typst/runs/132503365652
[security-receiving-quality-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43613548339
[security-receiving-maintenance-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43613547923
[security-receiving-privacy-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43613547805
[security-receiving-codeql-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43613547696
[security-receiving-graph-run]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43613554074
[document-contract]: https://github.com/edithatogo/unimelb-thesis-template-typst/issues/14

[receiving-coverage-job]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43613547923/job/132503590597
[receiving-upload-job]: https://github.com/edithatogo/unimelb-thesis-template-typst/actions/runs/43613547923/job/132516395426
[receiving-statuses]: https://api.github.com/repos/edithatogo/unimelb-thesis-template-typst/commits/937579897af22d7d28f20a49e94a1bdbe4e05855/statuses
[receiving-codecov]: https://app.codecov.io/gh/edithatogo/unimelb-thesis-template-typst/commit/937579897af22d7d28f20a49e94a1bdbe4e05855

[central-classification-merge]: https://github.com/edithatogo/repository-standards/commit/e195af3b0f46db74e797c5bf2e177b7882085186
