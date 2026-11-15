# Your author project

This directory contains six author files. The styling library is installed
separately as `@local/unimelb-thesis-template:0.2.1`. Use Typst 0.15.1.

Edit `main.typ` for metadata, `chapters/introduction.typ` for content,
`assets/figures/example.svg` for the example image, and `references.bib` for
references. The student, institution unit, source and geometric illustration are
synthetic demonstrations. Replace them before academic use.

The initializer retains this README and the Apache-2.0 licence. It does not copy
repository CI, tests, source evidence, bundled fonts, generated PDFs or caches.

With the same local package directory used during installation:

```sh
typst compile --package-path /absolute/path/to/packages --root . main.typ thesis.pdf
typst watch --package-path /absolute/path/to/packages --root . main.typ thesis.pdf
typst compile --package-path /absolute/path/to/packages --root . --input profile=draft main.typ draft.pdf
```

Add another chapter file and include it from `main.typ`. Keep caller resources
as native `path(...)` values when passing them to package helpers; strings are
resolved in the file or package that reads them. The example demonstrates a
nested figure and a bibliography owned by this directory.

The starter selects `font_theme: "classic"` and does not distribute font files.
For a reproducible local baseline, the packaging verifier disables system fonts
and records observed PDF font names/embedding. Other themes and writing systems
need their own installed fonts and validation.

Read the maintained project guides for optional public disclosures, blind review,
source checks, and submission preparation:
https://github.com/edithatogo/unimelb-thesis-template-typst

Compilation does not certify institutional policy, accessibility, anonymity,
rights or approval. Review the final PDF and required deposit materials yourself.
