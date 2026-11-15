# COR-04: managed identity and authored residuals

These Apache-2.0 fixtures contain synthetic identifiers only. The legacy
`thesis(..., blind: true)` entry point projects resolved metadata once, after
overrides and before document metadata, context and pages consume it. Identified
output retains its original metadata and content. `blind` accepts a boolean;
the string `"false"` is rejected.

## Projection boundary

Blind rendering replaces author/signature, department, school, institution and
supervisor fields with neutral labels, removes co-supervisor names, keywords and
acknowledgements, replaces the university banner, and disables branding. It
numbers contribution names and publication citations without forwarding original
publication links or unknown fields. Contribution roles/percentages and publication
status/consent remain visible. The original resolved object is not modified.

The title displays a static author-review notice. A queryable metadata element
with label `<blind-review-diagnostics>` reports `author-review-required` and names
the content areas requiring review. The notice/diagnostic contains no original
identifiers and certifies neither anonymity nor a reviewer-ready artifact.

The renderer preserves arbitrary author-written titles, abstracts, prefaces,
custom declarations, assistance disclosures, contribution-role text, body text,
captions, citations, images/alternative text, appendix content, index entries and
link targets. In particular, `index_entries` renders authored index terms; it is
explicitly named in the review diagnostic and is never claimed to be scrubbed.
It also cannot project raw publication/contribution collections passed directly
to helpers by a caller's body. Authors must supply reviewed neutral content where
appropriate; a warning is not a replacement for that review. The fixtures keep
these surfaces identifiable in negative controls, including direct helper calls.

This increment does not implement the shared JSON contract adapter, determine
whether blind review is valid for examination/deposit, or implement a
reviewer-safe manifest/package. Full source/configuration identities and logs
remain internal evidence. Do not include them automatically in a reviewer
delivery; packaging is a separate workstream.

## Ten bounded cases

| Cases | Expected observation |
|---|---|
| Structured identified / blind | Named positive controls emit every declared structured marker; blind output retains role/percentage/status/consent and emits no declared identifier on inspected surfaces |
| Authored identified / blind | Body, preface, disclosure, citation, raw-helper, alt-text and URI identifiers remain present; the blind PDF's identity scan fails |
| Custom-declaration identified / blind | Supplied declaration text remains intact; the blind PDF's identity scan fails |
| Authored reviewed blind | Explicitly author-supplied neutral replacements retain content, a reference, alternative text and a resource link; no declared marker remains |
| Index identified / blind | The same identifying index term renders on the actual Index page; the blind scan fails and requires author review |
| Blind string rejected | Literal string `"false"` fails with the intended strict-boolean diagnostic and no PDF |

`scripts/verify.py` is the only canonical orchestrator. It keeps thesis/sample
checks and all earlier corpora, gives every external command 60 seconds, deletes
old outputs, and writes an initial failed/unexecuted report. COR-04 captures
qpdf native JSON, PDF Info/XMP, visible text, native bookmark/tag/alternative-text
and URI strings, dependencies, and the queryable diagnostic.

The pure oracle scans for the declared fixture identifiers, checks explicit
positive controls, and verifies neutral labels and retained semantic values.
The three residual blind PDFs are recorded with
`public_surface_scan.passed: false` and `result: fail`. Their regression assertions
pass only because the required leaks were detected on the expected surfaces.
They are never counted among the two clean blind controls. All cases retain
`reviewer_ready_certified: false`.

Run the integrated canonical gate from the full repository:

```sh
make verify
```

To inspect the static boundary notice for the synthetic blind specimen:

```sh
typst query --root . --input cor04-identity=blind \
  tests/rendered/cor04/structured-fields.typ \
  '<blind-review-diagnostics>' --field value
```

Known-marker scans cannot establish universal anonymization. They do not inspect
all possible encodings, identify people in image pixels, or qualify embedded
files, accessibility, metadata from unrelated exporters, or public/private
packaging. This small corpus has no embedded attachments; a missing identifier
in an unrendered input cannot be credited as a successful projection.
