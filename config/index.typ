// =================================
// Modular Config Layer
// =================================

// Import all config modules
#import "metadata.typ": *
#import "publications.typ": *
#import "abbreviations.typ": *
#import "appendix.typ": *
#import "contributions.typ": *
#import "../utils/style.typ": colors

// =================================
// Automated Index System
// =================================

// State for tracking index terms and their page references
#let _index-terms = state("index-terms", (:))
#let _index-page-references = state("index-page-references", (:))

// Mark a term for inclusion in the index
// Usage: #index-term("machine learning") or #index-term("machine learning", category: "AI")
// Registration retains supplied page values; it never invents their location.
#let register-index-term(term, pages, category: none, subterm: none) = {
  assert(
    type(term) == str and term.trim() != "",
    message: "Index term must be a nonempty string.",
  )
  assert(
    subterm == none or (type(subterm) == str and subterm.trim() != ""),
    message: "Index subterm must be a nonempty string.",
  )
  assert(
    category == none or (type(category) == str and category.trim() != ""),
    message: "Index category must be a nonempty string.",
  )
  _index-terms.update(terms => {
    let current = terms.at(term, default: (
      category: category,
      subterm: none,
      pages: (),
      subentries: (:),
    ))
    if subterm == none {
      current.pages = (current.pages + pages).dedup()
    } else {
      let existing = current.subentries.at(subterm, default: ())
      current.subentries.insert(subterm, (existing + pages).dedup())
    }
    if category != none { current.category = category }
    terms.insert(term, current)
    terms
  })
}

// Invisible marker at the actual document location, with a logical page label.
#let index-term(term, category: none, subterm: none) = context {
  let loc = here()
  let pattern = loc.page-numbering()
  let value = counter(page).get().first()
  let page-label = if pattern == none or pattern == "1" { value } else {
    numbering(pattern, value)
  }
  register-index-term(term, (page-label,), category: category, subterm: subterm)
  metadata((
    type: "index-term",
    term: term,
    category: category,
    subterm: subterm,
  ))
}

#let extract-index-terms(content) = {
  let terms = ()

  // Pattern for capitalized terms (potential proper nouns, concepts)
  let capitalized-pattern = regex("([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)")
  let matches = content.matches(capitalized-pattern)

  for match in matches {
    let term = match.text.trim()
    // Filter out common words and very short terms
    let exclude-words = (
      "the",
      "and",
      "for",
      "are",
      "but",
      "not",
      "you",
      "all",
      "can",
      "had",
      "her",
      "was",
      "one",
      "our",
      "out",
      "day",
      "get",
      "has",
      "him",
      "his",
      "how",
      "its",
      "may",
      "new",
      "now",
      "old",
      "see",
      "two",
      "way",
      "who",
      "boy",
      "did",
      "has",
      "let",
      "put",
      "say",
      "she",
      "too",
      "use",
    )
    if term.len() >= 3 and lower(term) not in exclude-words {
      if term not in terms {
        terms.push(term)
      }
    }
  }

  terms
}

// Auto-extract index terms from document content
#let auto-extract-index(content, min-length: 3, exclude-words: ()) = {
  panic(
    "Automatic index extraction is unsupported. Mark actual locations with index-term(term), or supply explicit page references to optional-index-page(). extract-index-terms(string) provides suggestions only.",
  )
}

// Data helpers require a context, supplied by the index-page renderer.
#let get-index-terms() = { _index-terms.final() }

#let get-term-references(term) = {
  let data = get-index-terms().at(term, default: none)
  if data == none { () } else { data.pages }
}

#let format-page-references(pages) = {
  if pages.len() == 0 { return "" }
  if not pages.all(p => type(p) == int) {
    return pages.dedup().map(str).join(", ")
  }
  let sorted-pages = pages.sorted().dedup()
  let ranges = ()
  let start = sorted-pages.first()
  let previous = start
  for page in sorted-pages.slice(1) {
    if page == previous + 1 { previous = page } else {
      ranges.push(if start == previous { str(start) } else {
        str(start) + "-" + str(previous)
      })
      start = page
      previous = page
    }
  }
  ranges.push(if start == previous { str(start) } else {
    str(start) + "-" + str(previous)
  })
  ranges.join(", ")
}

#let generate-index-entry(term, pages, subterm: none, category: none) = {
  let formatted-pages = format-page-references(pages)

  if subterm != none {
    [#subterm, #formatted-pages]
  } else {
    [#formatted-pages]
  }
}

// Generate complete index with categorization
#let generate-index(
  include-categories: true,
  include-subentries: true,
  sort-by: "term",
) = {
  assert(
    sort-by in ("term", "category"),
    message: "Index sort-by must be term or category.",
  )
  let terms = get-index-terms()
  let names = if sort-by == "category" {
    terms
      .keys()
      .sorted(key: term => (
        if terms.at(term).category == none { "General" } else {
          terms.at(term).category
        },
        term,
      ))
  } else { terms.keys().sorted() }
  let result = (:)
  for term in names {
    let data = terms.at(term)
    if not include-categories { data.category = none }
    if not include-subentries { data.subentries = (:) }
    result.insert(term, data)
  }
  result
}

#let generate-index-page(
  title: "Index",
  include-categories: true,
  include-statistics: true,
  columns: 2,
  show-page-numbers: true,
) = context {
  assert(
    type(columns) == int and columns >= 1 and columns <= 4,
    message: "Index columns must be an integer from 1 to 4.",
  )
  set page(margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm))
  heading(title, numbering: none)
  v(1cm)
  let entries = generate-index(include-categories: include-categories)
  if entries.len() == 0 {
    [No index terms defined. Mark actual locations with index-term(term), or supply explicit manual page references.]
  } else {
    let body = {
      let previous-letter = none
      for (term, data) in entries.pairs() {
        let letter = upper(term.first())
        if letter != previous-letter {
          heading(letter, level: 2, numbering: none)
          previous-letter = letter
        }
        block({
          text(weight: "bold", term)
          if show-page-numbers and data.pages.len() > 0 {
            [ — #format-page-references(data.pages)]
          }
          for subterm in data.subentries.keys().sorted() {
            linebreak()
            h(1em)
            subterm
            if show-page-numbers {
              [ — #format-page-references(data.subentries.at(subterm))]
            }
          }
        })
        v(0.3em)
      }
    }
    if columns == 1 { body } else { std.columns(columns, gutter: 1em, body) }
    if include-statistics {
      v(1cm)
      let count = entries
        .values()
        .map(data => (
          data.pages.len()
            + data.subentries.values().map(p => p.len()).sum(default: 0)
        ))
        .sum(default: 0)
      text(
        size: 10pt,
        fill: gray,
      )[Index Statistics: #entries.len() unique terms, #count page references.]
    }
  }
}

#let validate-index() = {
  let terms = get-index-terms()
  let warnings = ()
  for (term, data) in terms.pairs() {
    if data.pages.len() == 0 and data.subentries.len() == 0 {
      warnings.push("Index term has no page references: " + term)
    }
  }
  (
    errors: (),
    warnings: warnings,
    total-terms: terms.len(),
    total-references: terms
      .values()
      .map(data => (
        data.pages.len()
          + data.subentries.values().map(p => p.len()).sum(default: 0)
      ))
      .sum(default: 0),
  )
}

#let get-index-stats() = {
  let validation = validate-index()
  (
    total: validation.total-terms,
    references: validation.total-references,
    errors: validation.errors.len(),
    warnings: validation.warnings.len(),
  )
}

// =================================
// Unified Config Interface
// =================================

// Main config dictionary exposing all modules
#let config = (
  // Metadata configuration
  metadata: (
    required-fields: required-fields,
    resolve: resolve,
  ),

  // Publications configuration
  publications: (
    statuses: statuses,
    validate: validate,
    publication-footnote: publication-footnote,
    publication-status-table: publication-status-table,
  ),

  // Abbreviations configuration
  abbreviations: (
    list: abbreviations,
  ),

  // Appendix configuration
  appendix: (
    appendix-counter: appendix-counter,
    reset-appendix-counter: reset-appendix-counter,
    appendix: appendix,
    creative-output-descriptor: creative-output-descriptor,
    appendix-summary: appendix-summary,
  ),

  // Contributions configuration
  contributions: (
    validate: validate-contribution,
    simple-table: simple-contribution-table,
    detailed-table: detailed-contribution-table,
    percentage-table: percentage-breakdown-table,
    ai-table: ai-contribution-table,
    matrix: contribution-matrix,
    sample: sample-contributions,
  ),

  // Index configuration
  index: (
    term: index-term,
    extract: extract-index-terms,
    auto-extract: auto-extract-index,
    get-terms: get-index-terms,
    get-references: get-term-references,
    format-references: format-page-references,
    generate: generate-index,
    generate-page: generate-index-page,
    validate: validate-index,
    stats: get-index-stats,
  ),
)

// =================================
// Helper Functions
// =================================

// Get a specific config module
#let get-config-module(name) = {
  config.at(name, default: none)
}

// Validate entire config against requirements
#let validate-config(metadata, publications: (), appendices: ()) = {
  // Validate metadata
  let resolved-metadata = config.metadata.resolve(metadata)

  // Validate publications
  let valid-publications = publications.map(config.publications.validate)

  // Validate appendices structure (basic validation)
  let valid-appendices = appendices

  (
    metadata: resolved-metadata,
    publications: valid-publications,
    appendices: valid-appendices,
  )
}
