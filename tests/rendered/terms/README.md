# Bounded glossary, abbreviation and index fixtures

These Apache-2.0 fixtures contain synthetic terms and explicit expectations.
The canonical verifier runs all 25 after the shipped thesis/sample PDFs and
earlier rendered corpora. Seventeen cases require validated rendered output;
eight require a specific diagnostic and no PDF. A passing rejection is recorded
as `document_result: rejected`, not as a clean document.

| Fixture group | Required public behavior |
| --- | --- |
| Abbreviations and page wrappers | All ten literal term/short-form/definition rows appear in the intended cells; first use expands once, later uses stay short, and an unexpanded use does not consume first expansion. |
| Glossary markers | Supplied definitions render once, repeated occurrences retain both logical page references, and links reach their own definitions. |
| Direct glossary index | All ten manual terms have visible index links targeting the corresponding definition, including distinct definitions on the same physical page. |
| Index markers and alias | Invisible markers retain actual locations; duplicate page references collapse; single/two-column outputs retain terms and subentries. |
| Manual entries | Explicit `2, 4-6` and subentry references survive unchanged; they are not replaced by the helper's physical page. |
| Edge cases | Roman/Arabic labels agree with native PDF labels; category ordering, empty output and hidden reference values behave explicitly. |
| Thesis integration | `thesis(index_entries: ...)` actually renders the supplied term and references after the body. |
| Eight rejections | Unsupported automatic extraction, invalid manual page values/ranges, empty terms and conflicting glossary definitions emit their intended diagnostics. |

`oracles.py` supplies literal values and pure assertions. It receives the existing
COR-02 native PDF parser from the verifier; both oracle and parser hashes are
retained. All positive cases retain qpdf JSON. Three glossary-link cases also
retain Poppler word bounding boxes. Each expected link is associated with its
visible source words and must have a resolvable native destination at its own
visible definition. The destination must be on the correct physical page,
within two points horizontally, and no more than twelve points above the
definition's first glyphs. Missing links or destinations fail explicitly.

This coordinate check distinguishes two entries on the same page. The bounded
negative controls remove expected annotations, create an unresolved destination,
and redirect Citation to Abstract on the same target page. Each must fail.

The canonical runner keeps the existing 60-second limit for every external
command, hashes source/fixtures/inputs/oracles and outputs, clears stale generated
artifacts, and writes an initial failed report. A rejected specimen must exit
exactly 1, emit only its intended diagnostic, avoid timeout, and leave no PDF.
Unrelated compiler failures and unexpected successful output cannot pass.

These checks establish bounded rendered behavior. They do not identify technical
terms from arbitrary prose, validate every user vocabulary, qualify all page
numbering functions, certify accessibility or establish university policy
acceptance. Run the full repository gate with `make verify` after integration.
