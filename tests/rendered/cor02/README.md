# COR-02 PDF navigation fixtures

The canonical `scripts/verify.py` runs these three specimens after the shipped
thesis/sample PDFs and all 14 COR-01 specimens. Use `make verify` for the full
repository gate. Every compiler, qpdf and Poppler command has a 60-second limit.

| Specimen | Required behavior |
| --- | --- |
| `navigation.typ` | Two chapters, nested level-2/3 headings, two appendices and their subsections appear in order in the contents and bookmarks. Their internal destinations reach the visible headings. Front-matter labels are Roman; Arabic labels restart at the first chapter and continue through the appendices. Forward/back chapter links and figure/table/algorithm list links remain valid. |
| `appendix-pages.typ` | An existing Arabic page counter at 7 continues as 7, 8, 9. Appendix A/B identify headings rather than changing page labels to letters. |
| `appendix-layout.typ` | Direct appendix-layout use compiles, retains native heading levels and bookmarks, and targets the rendered body pages. |

The navigation specimen also supplies four synthetic creative-descriptor
fields. The appendix must render separate Attribute/Details header cells and
exactly one Medium, Dimensions, Duration and Description row with the supplied
values. Source-fragment rejection is restricted to the controlled appendix
page. This tests supplied content; it makes no creative-work applicability or
institutional-policy determination.

`oracles.py` contains literal expectations and PDF parsers, without subprocesses
or compilation. It maps qpdf page-object references and named destinations to
physical pages, expands PDF page-label ranges, and checks bookmark hierarchy.
Unique body sentences independently identify the expected destination pages.
Poppler bounding boxes associate each contents row with its link annotations.
Native XYZ destinations must fall between one point below and 24 points above
the target heading's glyph box, distinguishing headings sharing a physical
page. Listing links are checked for their physical destination pages.

The contents-row parser permits the native outline's zero-width U+2060 WORD
JOINER immediately before a page label. It retains literal heading, order,
cardinality and page-number expectations. Missing bounding boxes, incomplete
oracle results and malformed or unsupported native structures fail closed.

Only these specimens require qpdf JSON and Poppler bounding-box extraction.
The verifier retains those files, extracted text, per-case oracle reports,
commands, diagnostics, source/fixture/oracle hashes and PDF hashes under
`build/verification/cor02/`. Stale outputs are removed before execution, and the
top-level report starts failed so interruption cannot preserve an earlier pass.

The corpus uses synthetic data, embedded compiler fonts and a fixed creation
timestamp. It establishes bounded navigation/content behavior, not general PDF
accessibility, arbitrary-thesis conformance, or document-wide reproducibility.
The fictional fixtures are distributed under the repository's
[Apache-2.0 licence](../../../LICENSE).
