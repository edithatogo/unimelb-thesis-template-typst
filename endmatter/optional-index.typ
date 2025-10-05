// Optional Index Generation Module
// This module provides automatic index generation and management
// Include this in your thesis configuration to enable optional index features

#import "../utils/style.typ": colors

// Index entry function for marking terms in the document
// Usage: #index("term") or #index("term", "subterm")
#let index(term, subterm: none) = {
  // Store index entries in document metadata for later processing
  // This is a placeholder - full implementation would require Typst's query system
  // For now, this serves as documentation of the intended API

  // In a full implementation, this would:
  // 1. Store the term and location in document state
  // 2. Generate page references during final rendering
  // 3. Handle sub-entries and cross-references

  // Placeholder implementation - just returns invisible content
  metadata((type: "index-entry", term: term, subterm: subterm, location: here()))
  []
}

// Generate optional index page with manual entries
#let optional-index-page(
  custom-entries: (:),
  show-page-numbers: true,
  columns: 2
) = {
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
  )

  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      Index
    ]
  ]

  v(1cm)

  // Check if we have any entries
  if custom-entries.len() == 0 {
    text(fill: gray)[
      *Index Generation Note:* This index is currently empty. To populate the index:

      1. *Manual Entries*: Add entries to the `custom-entries` parameter when calling this function
      2. *Automatic Indexing*: Use `#index("term")` throughout your document (requires Typst query system)
      3. *Cross-references*: Include page numbers and sub-entries as needed

      *Example custom entries:*
      ```typst
      optional-index-page(custom-entries: (
        "Machine Learning": "15, 23, 45",
        "Neural Networks": "12, 34",
        "Deep Learning": "23, 67-69"
      ))
      ```
    ]
  } else {
    // Generate index from custom entries
    let sorted-terms = custom-entries.keys().sorted()

    // Group terms by first letter for better organization
    let grouped-terms = (:)
    for term in sorted-terms {
      let first-letter = upper(term.at(0))
      if first-letter not in grouped-terms {
        grouped-terms.insert(first-letter, ())
      }
      grouped-terms.at(first-letter).push(term)
    }

    // Display index in columns
    if columns == 1 {
      // Single column layout
      for letter in grouped-terms.keys().sorted() {
        heading(letter, level: 3, numbering: none)
        for term in grouped-terms.at(letter) {
          let pages = custom-entries.at(term)
          block[*#term*#if show-page-numbers [, #pages]]
          v(0.3em)
        }
        v(0.5em)
      }
    } else {
      // Multi-column layout - simplified version
      for letter in grouped-terms.keys().sorted() {
        heading(letter, level: 3, numbering: none)
        for term in grouped-terms.at(letter) {
          let pages = custom-entries.at(term)
          block[*#term*#if show-page-numbers [, #pages]]
          v(0.3em)
        }
        v(0.5em)
      }
    }
  }
}

// Advanced index with sub-entries support
#let optional-index-with-subentries(
  entries: (:),
  show-page-numbers: true,
  columns: 2
) = {
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
  )

  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      Index
    ]
  ]

  v(1cm)

  if entries.len() == 0 {
    text(fill: gray)[
      *Advanced Index Generation:* Use the `entries` parameter to define hierarchical index entries.

      *Example structure:*
      ```typst
      optional-index-with-subentries(entries: (
        "Machine Learning": (
          "supervised": "15, 23",
          "unsupervised": "45, 67",
          "definition": "12"
        ),
        "Neural Networks": (
          "backpropagation": "34",
          "activation functions": "56"
        )
      ))
      ```
    ]
  } else {
    // Generate hierarchical index
    let sorted-main-terms = entries.keys().sorted()

    // Group by first letter
    let grouped-terms = (:)
    for term in sorted-main-terms {
      let first-letter = upper(term.at(0))
      if first-letter not in grouped-terms {
        grouped-terms.insert(first-letter, ())
      }
      grouped-terms.at(first-letter).push(term)
    }

    // Display hierarchical index
    for letter in grouped-terms.keys().sorted() {
      heading(letter, level: 3, numbering: none)

      for main-term in grouped-terms.at(letter) {
        let sub-entries = entries.at(main-term)

        // Main term
        block[*#main-term*]
        v(0.2em)

        // Sub-entries (indented)
        for sub-term in sub-entries.keys().sorted() {
          let pages = sub-entries.at(sub-term)
          block[
            #h(1em)#sub-term#if show-page-numbers [, #pages]
          ]
          v(0.2em)
        }
        v(0.5em)
      }
      v(0.8em)
    }
  }
}

// Combined index and glossary helper
#let optional-index-glossary-page(
  index-entries: (:),
  glossary-terms: (:),
  show-statistics: true
) = {
  // Index section
  optional-index-page(custom-entries: index-entries, show-page-numbers: true)

  pagebreak()

  // Glossary section
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
  )

  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      Glossary and Index
    ]
  ]

  v(1cm)

  if glossary-terms.len() == 0 {
    text(fill: gray)[No glossary terms provided. Use the `glossary-terms` parameter to define terms.]
  } else {
    heading("Glossary", level: 2, numbering: none)

    let sorted-terms = glossary-terms.keys().sorted()
    for term in sorted-terms {
      let definition = glossary-terms.at(term)
      block[*#term*: #definition]
      v(0.5em)
    }

    if show-statistics {
      v(1cm)
      text(size: 10pt, fill: gray)[
        *Index and Glossary Statistics:* #index-entries.len() index entries, #glossary-terms.len() glossary terms
      ]
    }
  }
}