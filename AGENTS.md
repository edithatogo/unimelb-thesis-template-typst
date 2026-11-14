# Repository instructions

This is a solo-maintainer Typst thesis template. These instructions apply to the
whole repository. Keep changes focused and preserve existing thesis interfaces.

## Scope and sources

- `thesis.typ` and `sample-chapter.typ` are the primary build inputs.
- `lib.typ`, `utils/`, `layouts/`, `pages/` and front/end matter define the template.
- `scripts/` contains maintenance and validation tools; `tests/` tests those tools.
- `typst.toml` records the package and Typst version.
- Read the issue, current main, open PRs and relevant instructions before editing.
  Preserve other contributors' work and reconcile overlapping ownership.
- Keep examples and tests synthetic. Never commit private theses, research data,
  credentials, personal notes or generated PDFs containing private material.

## Validation

Run `make verify` from the repository root. It runs Python tests, template and
package checks, bounded properties, desired ruleset validation and thesis/sample
PDF validation. The existing Typst CI checks formatting and all four thesis
profiles. See [CONTRIBUTING.md](CONTRIBUTING.md) for tools.

Use `make verify-python` or `make verify-typst` for focused development;
complete `make verify` before declaring the change verified. Inspect affected PDF
pages when layout changes. Report exact commands, commit and hosted run links.
If a runtime or service is unavailable, state what was not executed.

`make coverage` measures the Python validation tools listed in the coverage
configuration. It does not measure Typst layout correctness or every helper.
A valid desired ruleset file does not prove that GitHub has activated it.

## Automation and maintenance

- Fail closed on compilation, validation, test and coverage errors. Fix failures;
  do not weaken gates, delete tests or turn errors into warnings to obtain green CI.
- Keep mandatory approving reviews at zero. Do not introduce CODEOWNERS approval,
  required reviewers or team gates.
- Require only checks demonstrated on the proposed commit, with stable names and
  the expected app identity. Keep bots subject to the same automated gates.
- Pin external Actions to full commit SHAs and use the minimum job permissions.
  Publishing remains tag-only; ordinary branch pushes must not publish releases.
- Keep Renovate's shared preset and verify bot health before changing updater
  coverage. Do not create competing dependency bots.
- Preserve the offline-security provisioning and integration conditions in
  [PR #9](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/9).
  Cancelled or unexecuted offline jobs are not passing evidence.
- Retain owner recovery for emergencies, record why it was used and restore
  normal checks afterwards. Never use recovery to disguise a failed check.

See [SECURITY.md](SECURITY.md) for confidential reports and
[docs/maintenance.md](docs/maintenance.md) for ruleset activation and drift evidence.
