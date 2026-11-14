# Contributing

Run `make verify`, inspect the generated PDFs, and include the hosted CI link.
The command requires Python 3.11+, the Typst version in `typst.toml`, qpdf
and Poppler. Source-only checks can be run with `make verify-source`;
they do not replace compiler checks.

See [Quality gates and bounded testing](docs/quality-gates.md) for property
replay commands, CI budgets, evidence retention and coverage limitations.

Automated checks replace mandatory human approval for this solo-maintainer
template.
