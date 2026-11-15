# Glossary, abbreviation and index rendering

This bounded repair addresses actual values, first use, page references and
native glossary links in the existing helpers. It contributes to the rendering
work in [issue 15](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/15);
broader policy, accessibility and shared-contract adapter acceptance remain open.

## Abbreviations and explicit glossary markers

`abbreviation-table()` and the page wrappers now render separate cell values.
`abbrev("ML")` expands the first occurrence to `Machine Learning (ML)` and later
occurrences to `ML`. Passing `expand: false` emits the short form without
consuming the later first expansion.

`glossary("Citation")` uses an existing manual definition, expands its first use
when requested, and records repeated logical page references. Use `link: false`
when a glossary destination is not being rendered. For explicit new definitions,
mark each actual occurrence and render the target glossary:

```typst
#import "config/glossary.typ": glossary-term, generate-glossary-page

An explicit #glossary-term("Synthetic Concept", "A supplied definition.")
appears here.

#pagebreak()
#generate-glossary-page(
  include-abbreviations: false,
  include-manual-glossary: false,
)
```

Repeated markers preserve a single definition and all observed page labels.
Conflicting definitions reject with an explicit diagnostic. A linked marker
requires a rendered destination; a missing target is an error. The direct
`generate-glossary-index()` renderer supplies its own context and links its terms
to the generated definitions.

## Index markers and supplied references

`index-term("Synthetic Concept")` records an invisible marker at its actual
location. The `index(...)` alias uses the same registration. A `subterm` retains
its own references rather than replacing another subentry. Page-reference
formatting deduplicates numeric pages and compresses consecutive integers;
mixed Roman/Arabic labels retain their observed order.

Manual references remain supplied data. For example:

```typst
#import "endmatter/optional-index.typ": optional-index-page

#optional-index-page(
  custom-entries: (
    "Synthetic Alpha": "2, 4-6",
    "Synthetic Beta": (3, 8),
  ),
  columns: 1,
)
```

Comma-separated strings accept individual positive integers and ordered ranges
with a hyphen or en dash. Integer arrays are also accepted. Zero, negative or
invalid values and reversed ranges reject. These explicit references are not
replaced with the page where the helper is called. `show-page-numbers: false`
hides entry reference values while retaining the index content and optional
statistics. `thesis(index_entries: ..., include_index: true)` now forwards the
resolved entries to this renderer.

## Context and unsupported extraction

The rendering helpers supply their own contextual evaluation. Data-returning
helpers that read final document state require a caller `context`, including
`get-extracted-glossary`, `generate-full-glossary`, `get-index-terms`,
`get-term-references`, `generate-index`, `validate-index` and `get-index-stats`.
For example:

```typst
#import "config/index.typ": generate-index
#context {
  let entries = generate-index(sort-by: "category")
  // Consume entries as data within this context.
}
```

The former automatic-extraction placeholders are explicitly unsupported.
`auto-extract-glossary`, `extract-terms-from-content` and `auto-extract-index`
reject with migration guidance. They do not infer definitions or real document
locations. String-only `extract-technical-terms` and `extract-index-terms` may
provide suggestions; those suggestions do not register glossary definitions or
index references. Use explicit markers or supplied manual references instead.

The canonical [25-case corpus](../tests/rendered/terms/README.md) checks actual
PDF text, native page labels and glossary destinations. Expected rejections are
separate from the 17 successful-output cases. The complete repository gate and
applicable hosted checks must pass on the integrated source before that source
is treated as qualified.
