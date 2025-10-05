## Repo notes for AI coding agents

This repository is a Typst template for University of Melbourne theses. Keep changes small, document them, and prefer non-breaking edits to templates used by students.

Quick actionable commands
- Compile main thesis: `typst compile thesis.typ` (CI uses Typst v0.13)
- Watch for changes locally: `typst watch thesis.typ` or `./automate.sh watch`
- Quick compile of sample chapter: `typst compile sample-chapter.typ`
- Validate template and packages: `python scripts/validate_template.py` and `python scripts/check_packages.py`

Key files and where to look
- `thesis.typ` — project entrypoint and where authors set title/author/degree; prefer small, targeted edits here for content changes.
- `lib.typ` / `utils/style.typ` — global styles, fonts and macros. Change here when adjusting appearance or layout.
- `pages/` — per-page templates (title, abstract, acknowledgements, landscape samples). Use these for scaffolded page edits.
- `layouts/` — page layout definitions and margin rules.
- `assets/` — logos, colors, fonts (fonts are packaged under `assets/fonts`).
- `typst.toml` — template metadata and pinned Typst tool version.
- `scripts/*.py` — repository helpers (package checks, validation). Use them to surface issues before opening PRs.

Project-specific patterns to follow
- Typst package imports use this pattern in .typ files: `#import "@preview/<pkg>:<version>"`. Use `grep -R "#import \"@preview/" -n .` to find usages.
- Output artifact expected by CI and releases: `thesis.pdf` (also `sample-chapter.pdf` when applicable).
- Keep alterations to `thesis.typ` backward compatible; students rely on the template structure (title metadata, front-matter, and `#show: thesis.with(...)`).

CI and compatibility notes
- CI compiles `thesis.typ` and `sample-chapter.typ` and runs Python validators. Tests assume Typst v0.13; avoid introducing syntax that requires newer Typst features without updating `typst.toml` and CI workflow.
- The workflow also lints Markdown and builds docs under `docs/` (see `.github/workflows/ci-cd.yml`).

Typical developer workflows for PRs
1. Run `typst compile thesis.typ` locally and fix layout/compile errors.
2. Run `python scripts/check_packages.py` to ensure imports are consistent.
3. Update `README.md`/`QUICKSTART.md` if you add user-visible commands.
4. Keep PRs small and explain any changes to fonts/colors/layout in the PR description.

When to change what
- Small content changes: edit files in `pages/` or `thesis.typ`.
- Style/layout changes: edit `utils/style.typ`, `lib.typ`, or `layouts/` and include screenshots or generated `thesis.pdf` snippets in the PR.
- Dependency or toolchain bumps: update `typst.toml` and `.github/workflows/ci-cd.yml` together; include migration notes.

If you're unsure
- Rebuild locally and attach `thesis.pdf` to your draft PR. Reference the lines in `thesis.typ` you edited and run the Python validation scripts before opening PRs.

Feedback request: After reviewing these instructions, tell me if you want stricter rules (formatting/linting of Typst files), example PR templates, or automated checks added.

Debugging & quick checks
- If `typst compile thesis.typ` fails, first try compiling the sample chapter to narrow the issue:
	- `typst compile sample-chapter.typ`
- Check for package/import issues: `grep -R "#import \"@preview/" -n .` and run `python scripts/check_packages.py` to surface mismatched or unused package entries.
- If fonts cause layout issues, verify fonts exist in `assets/fonts/` and match `lib.typ`/`utils/style.typ` entries.
- For CI parity, ensure your local Typst version is compatible with `typst.toml` (CI uses v0.13) — run `typst --version` to check.

Common Typst compile errors and fixes

- "Unknown command or macro 'foo'": usually caused by a missing `#import` or a package version mismatch.
	- Fix: ensure the package is imported in the relevant `.typ` (search `#import "@preview/"`) and check versions in `typst.toml` / `scripts/check_packages.py`.

- "Font 'X' not found": Typst can't locate the font on the system or the font name doesn't match the family declared in `lib.typ`.
	- Fix: verify the font files are present in `assets/fonts/`, confirm names in `lib.typ`/`utils/style.typ`, and ensure CI installs fallback fonts if needed.

- "Layout overflow" or "page break" issues: overly wide floats/tables or long unbreakable content.
	- Fix: try `sample-chapter.typ` to reproduce, wrap long content, switch to a landscape sample (see `pages/landscape-sample.typ`), or adjust margins in `layouts/`.

CI artifacts and what to expect

- On package-check failure the CI will upload `check-packages.log` as an artifact so reviewers can inspect the script output.
- The CI will upload `thesis.pdf` and `sample-chapter.pdf` as compilation artifacts on successful (or attempted) builds — use these to verify layout changes in PRs.


