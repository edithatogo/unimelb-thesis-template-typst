# COR-02 contents and appendix navigation repair

This is the contents, appendix and PDF-navigation increment of
[issue #15](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/15).
It preserves native headings so their visible numbering, contents entries,
bookmarks and internal destinations describe the same document structure.

## Repaired behavior

The contents page selects the document's headings, has one visible title, and
does not list itself. Its title remains a bookmark. Appendix rendering evaluates
the supplied content, uses the current contextual interface, and retains each
native heading instead of constructing a replacement inside its own show rule.
Appendix headings use `Appendix A:`, `Appendix B:` and subordinate `A.1`, `B.1`
numbers. Their logical page labels continue the main text's Arabic sequence.

The public appendix sequence remains independent of preceding chapter numbers.
Direct appendix-page and appendix-layout calls remain supported. The repaired
path also exposes the existing creative descriptor, whose supplied field/value
rows now occupy separate table cells. Creative applicability is unchanged.

## Executable evidence

The [three synthetic specimens](../tests/rendered/cor02/README.md) run through
the existing `make verify` command after the shipped thesis/sample and all 14
COR-01 specimens. Each compiler/PDF command retains its 60-second limit.

The navigation oracle compares independently specified headings, hierarchy,
page labels and destination text against actual qpdf JSON, extracted PDF text
and Poppler bounding boxes. It checks contents rows, forward/back references,
figure/table/algorithm lists, and bookmark destinations. A coordinate check
distinguishes two headings on the same physical page. The direct appendix
specimens check numbering and compatibility without the full thesis wrapper.
The verifier records source, fixture, oracle and output hashes with commands,
diagnostics and native sidecars. Missing or malformed evidence fails the gate.

Development probes against source `bffb278b3bc8e05c5686a047cf5e0fc67913857b`
confirmed an empty contents list, duplicate contents title, literal appendix
call and absent appendices. That PDF compiled and passed structural checks but
failed 28 navigation assertions. Direct appendix-page and appendix-layout
probes failed to compile. Compatibility probes then exposed obsolete callback,
heading-parameter, spacing-key and recursive-show-rule behavior.

The repaired prototype passed 198 assertions across the three specimens. A
second negative control retained the old creative-descriptor helper and failed
14 descriptor assertions while the two direct appendix specimens passed. An
in-memory destination fault also demonstrated that the oracle rejects a
bookmark redirected to the wrong heading on the same physical page. These are
bounded development observations; final source and receiving qualification are
recorded in the PR and issue checkpoint.

## Remaining acceptance

This increment does not complete COR-02 or COR-05. Glossary/abbreviation first
use, index behavior, automatic extraction, bibliography policy, configuration
propagation and independent optional-section applicability retain their own
acceptance. Native navigation checks do not establish accessibility conformance
or institutional approval. The exported, currently unused `appendix-summary`
helper is outside these specimens and remains a separate content concern.
