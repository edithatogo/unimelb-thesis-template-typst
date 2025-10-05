// Basic Index Template
// This file provides a simple index page that can be customized
// For advanced indexing features, use the optional-index.typ module

#import "../utils/style.typ": colors

// Basic index page with placeholder content
// This serves as a fallback when the optional index system is not used
#set page(
  margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
)

#align(center)[
  #text(size: 18pt, weight: "bold", fill: colors.primary)[
    Index
  ]
]

#v(1cm)

#text(fill: gray)[
  *Index Configuration Note:* This is a basic index template. For advanced indexing features including:

  - Automatic index generation from document content
  - Hierarchical entries with sub-terms
  - Multi-column layout options
  - Combined index and glossary pages

  Configure your thesis with `include_index: true` and use the optional index functions from `endmatter/optional-index.typ`.

  *Example usage in thesis.typ:*
  ```typst
  #show: thesis.with(
    // ... other metadata ...
    include_index: true,
    // Custom index entries can be provided via metadata_overrides if needed
  )
  ```

  *Manual index entries can be added here:*
]

// Placeholder for manual index entries
// Uncomment and customize as needed:
/*
#block[
  *Machine Learning* 15, 23, 45 \
  *Neural Networks* 12, 34 \
  *Deep Learning* 23, 67-69 \
  *Supervised Learning* 15, 28 \
  *Unsupervised Learning* 45, 52
]
*/

#pagebreak()
