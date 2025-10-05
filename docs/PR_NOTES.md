PR notes — summary of recent changes

Summary

- Fixed local font ordering in `utils/fonts.typ` to restore normal body weight.
- Created a runnable example at the repository root: `example-run.typ` and updated examples
  under `examples/` so they compile from the repo root.
- Added `scripts/compile_examples.sh` to run smoke compiles for key examples and thesis.
- Added a short `README.md` section explaining how to compile examples and the `--root .` usage.
- Added `docs/COMPATIBILITY_NOTES.md` describing why small, defensive edits were made to
  `config/glossary.typ` and `lib.typ` to make minimal examples more resilient.

Validation results

- `python3 scripts/validate_template.py` output:

  ✅ Directory structure is valid

  ✅ Required files are present

  ✅ Typst.toml is valid

  ❌ Primary brand color not found in color definitions

  ❌ Typst syntax issues found (potential let binding issues in several files). See validator
  output for file-level details.

- `python3 scripts/check_packages.py` output: No package usage issues found.

Recommended next actions for maintainers

- Decide whether to keep the defensive compatibility edits in core files or to revert them and
  provide example adapter wrappers. See `docs/COMPATIBILITY_NOTES.md` for rationale.
- Address the validator warnings (primary color missing and potential let-binding issues) as
  part of a follow-up cleanup PR. Those are not new regressions introduced by these small
  documentation/compatibility changes.
