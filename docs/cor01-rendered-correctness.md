# COR-01 rendered content repair

This is the declaration, contribution-table, publication-table and footnote
increment of [issue #15](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/15).
The existing public arguments and defaults remain available. The repair evaluates
the supplied content and constructs actual list items and table cells.

## Interface compatibility

| Interface | Repaired behavior |
| --- | --- |
| `declaration-page` | The two existing mandatory clauses are separate numbered items. Supplied word count, AI-use text and human-assistance text produce their existing optional clauses. Absent optional values produce no clause. |
| `contribution-table` | Dictionary and tuple entries still work. Each entry occupies one row with three cells; numeric percentages render as numbers. An empty collection produces no table. |
| `publication-status-table` | Citation, status and consent values occupy their declared columns. `show_links: true` adds a real appendix-reference cell. An empty collection produces no table. |
| `publication-footnote` | The supplied citation, status, consent and optional appendix text appear in the footnote. |
| `publication-chapter-footnote` | Both an integer index and a citation string resolve existing entries. A missing entry retains the existing explicit missing-entry note. |
| `publication-appendix-link` | Plain appendix descriptions retain a textual reference. A supplied anchor, a fragment string such as `#app-a`, or a simple identifier uses a native document label destination. |

Named appendix destinations require a matching Typst label. Explicit anchors may
be a string or a label value. This follows the native
[link destination interface](https://typst.app/docs/reference/model/link/).
The repaired helper uses the native
[string methods](https://typst.app/docs/reference/foundations/str/) when inferring
an identifier from appendix text.

Legitimate source-code examples remain supported. The regression specimens put
raw code on a separate control page, and check for unwanted source fragments only
in each component's expected output region.

## Creative declaration applicability remains open

The existing `includes_publications` argument still controls the creative-output
clause. Its existing wording and percentage inputs are preserved in this focused
repair. That argument does not establish whether creative outputs exist, and the
clause is not an institutional approval decision.

COR-05 must separate publication and creative-output applicability and establish
the appropriate declaration inputs. This increment does not complete that work.
The remaining configuration, navigation, blind-output and policy requirements in
issue #15 also remain open.

## Reproduction evidence

The baseline is commit `ee8fb8b3f973914b15198ba43d18048d2351cc17` with Typst
`0.15.1`. Twelve synthetic cases cover empty, one-entry and multiple-entry inputs
for the four interfaces. All twelve baseline PDFs compiled and passed structural
validation, while nine failed the expected rendered-content assertions. The
three empty table/footnote controls passed. This demonstrates why compilation
alone did not detect the problem.

The same twelve focused cases pass after the content repair. Separate direct
appendix probes also changed from compiler errors to valid output: the plain-text
path previously called a nonexistent string method, and the explicit-anchor path
passed an unsupported `href` argument to `link`.

The local investigation retains its baseline and repaired PDFs, extracted text,
exact commands, hashes and before/after page images under `build/cor01/`. The
focused repaired run is an observation of a working-tree change, not a receipt
for a merged revision. Final acceptance requires the canonical verifier and
applicable checks on the integrated revision.
