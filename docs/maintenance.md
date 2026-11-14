# Solo-maintainer maintenance

Issue [#5](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/5)
tracks source checks, protection settings, dependency updates and coverage.
The machine-readable [audit receipt](maintenance/issue-5-receipt.json) separates
observed settings from the intended configuration. A committed ruleset file
does not activate GitHub protection.

## Reproduce the checks

Install the tools and Python coverage dependency described in
[CONTRIBUTING.md](../CONTRIBUTING.md), then run from the repository root:

```sh
make verify
make coverage
```

The first command extends issue #4's canonical verification: unit tests, structural
and package checks, the bounded property suite, desired-policy validation, and
thesis/sample compilation with PDF integrity/text checks. The shared Typst matrix in Quality gates
separately checks formatting and all four thesis build profiles. It fails on any failing command.
The structural delimiter scan remains advisory; Typst compilation is the syntax
gate. Renovate, rather than the legacy package inventory script, checks updates.

Coverage is line and branch execution in `scripts/preflight.py`,
`scripts/validate_template.py` and `scripts/check_repository_policy.py`.
The 80% floor applies to those three validation tools only. Tests use synthetic
repositories and mocked compiler failures; the separate build invokes real
Typst. The report does not measure Typst/layout coverage, every Python helper,
or shell-script coverage. Reports are written to `build/coverage.xml` and
`build/coverage.json`.

The Maintenance workflow runs on every PR, pushes to main, merge groups,
manual dispatch and a weekly schedule. It retains coverage reports for 14 days;
the Quality gates workflow retains the compilation evidence and PDFs. The Maintenance workflow's separate upload job uses Codecov OIDC; only that job receives
`id-token: write`. Fork PRs still run checks and retain their evidence; they do
not enter the OIDC upload job. Upload errors fail the upload job.

## Dependency and bot inventory

Renovate's [Dependency Dashboard #7](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/7)
was observed with current workflow and Typst dependencies on 15 November 2026
(Brisbane time). `renovate.json` already inherits
`github>edithatogo/renovate-config`. There is no Dependabot configuration to
remove. Keep one updater per ecosystem and verify fresh bot-produced evidence
before changing update coverage.

GitHub Actions is the observed check producer (app ID 15368). The candidate
ruleset requires these exact contexts:

| Context | Purpose |
| --- | --- |
| `compile (default) / build` | Shared default-profile format/build/PDF check |
| `compile (draft) / build` | Existing draft-profile check |
| `compile (screen) / build` | Existing screen-profile check |
| `compile (print) / build` | Existing print-profile check |
| `privacy-and-secrets` | Existing Presidio and Gitleaks baseline |
| `Workflow lint` | Workflow syntax and shell validation from issue #4 |
| `Verify template and properties` | Canonical source, property, unit and PDF verification |
| `Python validation coverage` | Validation-tool tests, policy and coverage floor |

The compile, quality and coverage contexts have executed success on earlier
PR #10/#12 candidates; the receipt records their exact revisions and runs.
Require successful, completed runs on the current candidate before activating
this list. Check names alone, skipped jobs and queued runs are insufficient.
CodeQL default setup and Codecov have also produced successful results, but
those results do not qualify later commits. Verify their current-head results
separately. The conditional offline security pipeline remains outside the
required list until its infrastructure and integration are qualified.
No bot receives a ruleset bypass.

## Activate and verify protection

The intended configuration is
[`.github/rulesets/solo-maintainer.json`](../.github/rulesets/solo-maintainer.json).
It prevents default-branch deletion and force pushes, requires PRs and current
automated checks, requires review conversations to be resolved, and sets
mandatory approving reviews to zero. It adds no
CODEOWNERS or team-review gate. The sole recovery actor is repository owner
`edithatogo` (GitHub user ID 15080672), with audited `always` bypass rather than
`exempt` bypass.

[UMTHESIS GOV-01 and section 7](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13)
require conversation resolution while preserving zero mandatory approvals. The
policy validator rejects a missing pull-request rule and a false or omitted
`required_review_thread_resolution` setting. Verify the explicit `true` value
in the saved GitHub ruleset as part of settings readback.

As recorded in the baseline receipt, main was unprotected and the ruleset list
was empty. An authenticated settings inspection on 15 November 2026 confirmed
that no ruleset or classic branch-protection rule had yet been created.
Administration writes remain unavailable to the connector; the authenticated
settings interface can apply the policy after the final candidate checks pass.
Activation and full readback are still required.

After every candidate context has succeeded, an administrator can import the
JSON under repository **Settings → Rules → Rulesets**, or create it with:

```sh
gh api --method POST repos/edithatogo/unimelb-thesis-template-typst/rulesets \
  --input .github/rulesets/solo-maintainer.json
```

Re-read the ruleset list first. If this named ruleset now exists, compare its
full settings and update its existing ID rather than creating a duplicate.
Do not create an admin credential or grant additional app access just to run
this command in CI. GitHub's [rules REST API](https://docs.github.com/en/rest/repos/rules)
requires administration write permission for activation.

Export every full applicable ruleset, including bypass actors, into a JSON
array. The collection/list response contains summaries and is insufficient
when the list is nonempty. Then compare the fresh snapshot:

```sh
python3 scripts/check_repository_policy.py \
  --desired .github/rulesets/solo-maintainer.json \
  --observed build/observed-rulesets.json
```

The checker returns 0 for a matching supplied snapshot, 1 for drift, and 2 for
unknown/unreadable evidence. With `--desired` alone, success validates only the
intended policy. The checked-in empty baseline snapshot should produce drift:

```sh
python3 scripts/check_repository_policy.py \
  --desired .github/rulesets/solo-maintainer.json \
  --observed docs/maintenance/issue-5-observed-rulesets.json
```

Record the observation time, exact source commit, URLs, ruleset ID and outcome
when updating the receipt. This offline checker does not prove snapshot
freshness or cover separate legacy branch-protection settings; inspect those
as well. HTTP 403/404 and missing bypass evidence remain unknown.

Every observed ruleset must have recognized target/enforcement values and
correctly shaped fields before comparison. Malformed secondary observations
remain unknown even when the named policy matches. Additional active branch
or push rulesets yield drift for review because they can constrain main-branch
updates. Valid tag rulesets and non-enforcing (`disabled`/`evaluate`) secondary
rulesets are outside this branch-policy inventory; inspect release-tag rules
separately. A match does not validate every possible GitHub rule parameter.

Use owner recovery only to repair a lockout or broken policy. Record the reason,
affected commit, checks available at the time and restoration in an issue/PR.
Restore normal checks after recovery. Routine dependency updates use the same
automated gates as other changes.

## Outstanding external evidence

A successful coverage upload is only transport evidence. Verify that
[the Codecov repository](https://app.codecov.io/gh/edithatogo/unimelb-thesis-template-typst)
shows the report for the exact tested SHA, then inspect GitHub for the resulting
`codecov/project` or `codecov/patch` context. Keep the issue open until both
service activation and commit-status evidence are recorded.

The 15 November 2026 snapshot records successful OIDC upload and a Codecov-owned
`codecov/patch` check (app ID 254) for
`66beec5cd7b78a9cdc1aad37dd288350184ef14d`, with 98.80% of the diff covered
against the 80% target. This establishes that the service processed that
repository/commit. The subsequent policy-checker fix needs its own hosted
coverage and service result; protection activation/readback remains outstanding.

The authenticated [Advanced Security settings](https://github.com/edithatogo/unimelb-thesis-template-typst/settings/security_analysis)
inspection on 15 November 2026 confirmed that private vulnerability reporting,
Dependabot alerts and secret push protection are enabled. Dependabot security
updates are also enabled, although no version-update configuration exists.
Renovate's inherited preset enables vulnerability handling; dashboard activity
alone does not establish its effective alert permissions or security-fix
execution. Preserve the existing security-update coverage until a replacement
is qualified, and do not claim that no security-update capabilities overlap.
Follow [SECURITY.md](../SECURITY.md) for confidential reports.
[PR #9](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/9) retains
its isolated-runner, pinned-image, local-GLiNER and real-integration conditions.
The issue #5 changes do not satisfy those conditions.
