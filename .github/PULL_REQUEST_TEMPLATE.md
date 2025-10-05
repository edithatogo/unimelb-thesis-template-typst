<!-- Describe the purpose of this pull request and link any relevant issue. -->

Summary of changes:

- (short description)

Example PR title/body (copy & paste)

Title: Fix font mapping in utils/style.typ

Body:

- What: Corrected font family mapping to use Fraunces variable font in
  `utils/style.typ`.
- Why: The previous mapping caused fallback fonts to be used on Linux CI.
- Validation: Compiled `sample-chapter.typ` locally and attached `thesis.pdf`.

Checklist for contributors

- [ ] I ran `typst compile thesis.typ`.
- [ ] For chapter/layout changes, I also ran `typst compile sample-chapter.typ` and
  verified the PDF renders as expected.
- [ ] I ran `python scripts/check_packages.py` and addressed any issues it
  reported.
- [ ] For style/layout changes: I attached the generated `thesis.pdf` or a
  screenshot of the affected pages to this PR.
- [ ] I kept changes minimal and documented any edits to fonts, colors, or
  layouts in the PR description.

Notes for reviewers

- Prefer small, incremental PRs for layout or font changes.
  If a change affects many pages, include a brief migration note and a compiled
  `thesis.pdf` snapshot.

