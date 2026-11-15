# COR-01 rendered fixtures

The canonical `scripts/verify.py` compiles this deterministic synthetic corpus
after checking the shipped thesis and sample PDFs. Every command retains the
existing 60-second limit. Use `make verify` for the complete repository gate.
The fixtures contain fictional data and are distributed under the repository's
[Apache-2.0 licence](../../../LICENSE).

The corpus has 14 specimens:

| Component | Inputs | Expected content |
| --- | --- | --- |
| Declaration | Empty, one, multiple optional values | Two mandatory clauses; then the word-count clause; then AI and human-assistance clauses. Enumeration contains 2, 3 and 5 items respectively. |
| Contributions | Empty, one, multiple rows | Dictionary and positional-row values, with each complete row appearing exactly once. |
| Publication table | Empty, one, multiple rows | Citation, status and consent cells with exact row cardinality. |
| Publication footnotes | Empty, one, multiple entries | Direct notes and integer/citation chapter lookups. Alpha occurs three times when present; Beta occurs once in the multiple-entry specimen. |
| Appendix references | Plain text, native label | The optional table column, plain `Appendix A`, a native label destination and the explicit-anchor call. |

Page 1 is the controlled component region. Page 2 deliberately renders a raw
`v.at(...)` example. Oracles reject source fragments only in the component
region and require the raw example to survive on page 2. Empty table/note
controls must have no rows; the empty declaration retains its mandatory clauses.

`oracles.py` contains expected literal values, occurrence counts and checks. It
does not launch commands. The verifier removes its own stale outputs, checks
each PDF with qpdf and Poppler, and writes commands, tool identities, source and
fixture hashes, extracted text, output hashes and failures under
`build/verification/`. Fixture compilation uses embedded compiler fonts and a
fixed creation timestamp; this is a controlled semantic corpus, not a general
thesis reproducibility claim.

The retained development baseline lives separately under `build/cor01/baseline/`.
These checks target COR-01. Navigation, blind output and broader applicability
remain with their respective implementation work.
