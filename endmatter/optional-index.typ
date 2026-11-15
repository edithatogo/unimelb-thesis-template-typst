// Optional Index Generation Module
// This module provides automatic index generation and management
// Include this in your thesis configuration to enable optional index features

#import "../utils/style.typ": colors
#import "../config/index.typ": (
  auto-extract-index, extract-index-terms, format-page-references,
  generate-index, generate-index-page, get-index-stats, get-index-terms,
  get-term-references, index-term, register-index-term, validate-index,
)

// Index entry function for marking terms in the document
// Usage: #index("term") or #index("term", "subterm")
#let index(term, subterm: none) = { index-term(term, subterm: subterm) }

#let parse-index-pages(pages) = {
  let result = ()
  if type(pages) == array {
    result = pages
  } else {
    assert(
      type(pages) == str,
      message: "Manual index pages must be a comma-separated string or an integer array.",
    )
    for piece in pages.split(",") {
      let token = piece.trim().replace("–", "-")
      assert(
        token.match(regex("^[0-9]+(-[0-9]+)?$")) != none,
        message: "Invalid manual index page reference: " + token,
      )
      let ends = token.split("-").map(int)
      if ends.len() == 1 { result.push(ends.first()) } else {
        assert(
          ends.last() >= ends.first() and ends.last() - ends.first() <= 10000,
          message: "Manual index range must be ordered and contain at most 10001 pages.",
        )
        result += range(ends.first(), ends.last() + 1)
      }
    }
  }
  assert(
    result.all(p => type(p) == int and p > 0),
    message: "Manual index page numbers must be positive integers.",
  )
  result.sorted().dedup()
}

#let optional-index-page(
  custom-entries: (:),
  show-page-numbers: true,
  columns: 2,
) = {
  for (term, pages) in custom-entries.pairs() {
    register-index-term(term, parse-index-pages(pages), category: "manual")
  }
  generate-index-page(
    title: "Index",
    include-categories: true,
    include-statistics: true,
    columns: columns,
    show-page-numbers: show-page-numbers,
  )
}

#let optional-index-with-subentries(
  entries: (:),
  show-page-numbers: true,
  columns: 2,
) = {
  for (term, subentries) in entries.pairs() {
    for (subterm, pages) in subentries.pairs() {
      register-index-term(
        term,
        parse-index-pages(pages),
        category: "manual",
        subterm: subterm,
      )
    }
  }
  generate-index-page(
    title: "Index with Sub-entries",
    include-categories: true,
    include-statistics: true,
    columns: columns,
    show-page-numbers: show-page-numbers,
  )
}

#let optional-index-glossary-page(
  index-entries: (:),
  glossary-terms: (:),
  show-statistics: true,
) = {
  for (term, pages) in index-entries.pairs() {
    register-index-term(term, parse-index-pages(pages), category: "manual")
  }
  assert(
    glossary-terms.len() == 0,
    message: "The combined helper does not accept custom glossary definitions. Use glossary-term(term, definition) and generate-glossary-page() explicitly.",
  )
  generate-index-page(
    title: "Index",
    include-categories: true,
    include-statistics: show-statistics,
    columns: 2,
  )
  pagebreak()
  import "../config/glossary.typ": generate-glossary-page
  generate-glossary-page(
    title: "Glossary",
    include-abbreviations: false,
    include-manual-glossary: true,
    include-extracted-terms: false,
    show-statistics: show-statistics,
  )
}
