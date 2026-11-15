#import "../utils/style.typ": *

// Glossary System for Academic Writing
// Provides comprehensive glossary management with cross-referencing and validation

// Default glossary entries (can be extended by users)
#let glossary-entries = (
  (
    term: "Thesis",
    definition: "A long piece of writing on a particular subject, especially one that is done for a higher college or university degree.",
    category: "Academic",
    related: ("Dissertation", "Research"),
  ),
  (
    term: "Methodology",
    definition: "The system of methods followed in a particular discipline or field of study.",
    category: "Research",
    related: ("Method", "Approach"),
  ),
  (
    term: "Literature Review",
    definition: "A scholarly paper that includes the current knowledge including substantive findings, as well as theoretical and methodological contributions to a particular topic.",
    category: "Research",
    related: ("Review", "Bibliography"),
  ),
  (
    term: "Hypothesis",
    definition: "A supposition or proposed explanation made on the basis of limited evidence as a starting point for further investigation.",
    category: "Research",
    related: ("Theory", "Proposition"),
  ),
  (
    term: "Peer Review",
    definition: "The evaluation of work by one or more people with similar competencies as the producers of the work.",
    category: "Academic",
    related: ("Review", "Evaluation"),
  ),
  (
    term: "Citation",
    definition: "A reference to a source of information used in a scholarly work.",
    category: "Academic",
    related: ("Reference", "Bibliography"),
  ),
  (
    term: "Plagiarism",
    definition: "The practice of taking someone else's work or ideas and passing them off as one's own.",
    category: "Academic",
    related: ("Academic Integrity", "Ethics"),
  ),
  (
    term: "Abstract",
    definition: "A brief summary of a research article, thesis, review, conference proceeding, or any in-depth analysis of a particular subject.",
    category: "Academic",
    related: ("Summary", "Synopsis"),
  ),
  (
    term: "Bibliography",
    definition: "A list of the books referred to in a scholarly work, typically printed as an appendix.",
    category: "Academic",
    related: ("References", "Works Cited"),
  ),
  (
    term: "Appendix",
    definition: "A section at the end of a book or document containing additional information.",
    category: "Academic",
    related: ("Supplement", "Addendum"),
  ),
)

// State for tracking extracted terms and their page references
#let _extracted-terms = state("extracted-terms", (:))
#let _term-page-references = state("term-page-references", (:))
#let _glossary-used = state("glossary-used", (:))
#let native-glossary-link = std.link

// Call from a contextual renderer; page counters are logical, not physical.
#let record-glossary-page(term) = {
  let loc = here()
  let pattern = loc.page-numbering()
  let page-number = counter(page).get().first()
  let page-label = if pattern == none or pattern == "1" { page-number } else {
    numbering(pattern, page-number)
  }
  _term-page-references.update(references => {
    let pages = references.at(term, default: ())
    if page-label not in pages { pages.push(page-label) }
    references.insert(term, pages)
    references
  })
}

// Mark a term for automatic glossary inclusion
// Usage: #glossary-term("Machine Learning", "A method of data analysis...")
#let glossary-term(
  term,
  definition,
  category: "General",
  related: (),
) = context {
  assert(
    type(term) == str and term.trim() != "",
    message: "Glossary term must be a nonempty string.",
  )
  assert(
    type(definition) == str and definition.trim() != "",
    message: "Glossary definition must be a nonempty string.",
  )
  let current = _extracted-terms.get()
  if term in current {
    assert(
      current.at(term).definition == definition,
      message: "Conflicting definitions for glossary term: " + term,
    )
  }
  _extracted-terms.update(terms => {
    let entry = (
      term: term,
      definition: definition,
      category: category,
      related: related,
      auto-extracted: true,
    )
    if term not in terms { terms.insert(term, entry) }
    terms
  })
  record-glossary-page(term)
  native-glossary-link(label("glossary-" + term))[#term]
}

#let extract-technical-terms(text, min-length: 3, max-length: 50) = {
  // Simple pattern-based extraction (can be enhanced)
  // Look for capitalized words, technical patterns, etc.
  let patterns = (
    regex("[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*"), // Title case phrases
    regex("\\b[A-Z]{2,}\\b"), // Acronyms
    regex("\\b[a-z]+(?:-[a-z]+)+\\b"), // Hyphenated terms
  )

  let extracted = ()
  for pattern in patterns {
    let matches = text.matches(pattern)
    for match in matches {
      let term = match.text.trim()
      if (
        term.len() >= min-length
          and term.len() <= max-length
          and term not in extracted
      ) {
        extracted.push(term)
      }
    }
  }

  extracted
}

// Auto-extract terms from a block of content
#let auto-extract-glossary(content, category: "Auto-extracted") = {
  panic(
    "Automatic glossary extraction is unsupported. Mark terms with glossary-term(term, definition), then call generate-glossary-page().",
  )
}

// Data helpers require context supplied by their caller.
#let get-extracted-glossary() = {
  let extracted = _extracted-terms.final()
  let pages = _term-page-references.final()
  for term in extracted.keys() {
    let entry = extracted.at(term)
    entry.insert("page-references", pages.at(term, default: ()))
    extracted.insert(term, entry)
  }
  extracted
}

#let generate-full-glossary(
  include-auto-extracted: true,
  include-page-refs: true,
) = {
  let all-terms = (:)
  let pages = _term-page-references.final()
  for entry in glossary-entries {
    if include-page-refs {
      entry.insert("page-references", pages.at(entry.term, default: ()))
    }
    all-terms.insert(entry.term, entry)
  }
  if include-auto-extracted {
    for (term, entry) in get-extracted-glossary().pairs() {
      if term not in all-terms { all-terms.insert(term, entry) }
    }
  }
  all-terms.values().sorted(key: e => e.term)
}

#let validate-glossary() = {
  let errors = ()
  let warnings = ()

  // Check for required fields
  for entry in glossary-entries {
    if "term" not in entry {
      errors.push("Missing 'term' field in glossary entry")
    }
    if "definition" not in entry {
      errors.push(
        "Missing 'definition' field for term: "
          + entry.at("term", default: "unknown"),
      )
    }
  }

  // Check for duplicate terms
  let terms = glossary-entries.map(e => e.term)
  for (i, term) in terms.Enumerate() {
    for (j, other) in terms.enumerate() {
      if i < j and term == other {
        errors.push("Duplicate glossary term: " + term)
      }
    }
  }

  // Check for empty fields
  for entry in glossary-entries {
    if entry.term.trim() == "" {
      errors.push("Empty term found")
    }
    if entry.definition.trim() == "" {
      warnings.push("Empty definition for term: " + entry.term)
    }
  }

  (errors: errors, warnings: warnings)
}

// Get glossary term with auto-expansion on first use
#let glossary(term, link: true, expand: true, track-pages: true) = context {
  let entry = glossary-entries.find(e => e.term == term)
  if entry == none {
    text(fill: red, weight: "bold")[#term (?) ]
  } else {
    let used = _glossary-used.get()
    let first-use = expand and term not in used
    if first-use { _glossary-used.update(used => used + ((term): true)) }
    if track-pages { record-glossary-page(term) }
    let displayed = if first-use { [#entry.term (#entry.definition)] } else {
      [#entry.term]
    }
    if link {
      native-glossary-link(label("glossary-" + term), displayed)
    } else { displayed }
  }
}

#let get-glossary-term(term) = {
  glossary-entries.find(e => e.term == term)
}

// Search glossary by pattern
#let search-glossary(pattern, field: "term") = {
  glossary-entries.filter(entry => {
    let value = if field == "term" { entry.term } else if (
      field == "definition"
    ) { entry.definition } else if field == "category" {
      entry.at("category", default: "")
    } else { "" }
    value.contains(pattern)
  })
}

// Get glossary terms by category
#let get-glossary-by-category(category) = {
  glossary-entries.filter(entry => (
    entry.at("category", default: "") == category
  ))
}

// Get all categories
#let get-glossary-categories() = {
  let categories = glossary-entries.map(e => e.at(
    "category",
    default: "General",
  ))
  categories.dedup()
}

// Get sorted glossary entries
#let get-sorted-glossary(sort-by: "term", reverse: false) = {
  let sorted = glossary-entries.sorted(key: e => {
    if sort-by == "term" { e.term } else if sort-by == "category" {
      e.at("category", default: "ZZZ")
    } else { e.term }
  })
  if reverse {
    sorted.rev()
  } else {
    sorted
  }
}

// Get related terms for a glossary entry
#let get-related-terms(term) = {
  let entry = get-glossary-term(term)
  if entry != none and "related" in entry {
    entry.related
  } else {
    ()
  }
}

// Create cross-references between related terms
#let create-glossary-cross-references() = {
  for entry in glossary-entries {
    if "related" in entry {
      for related in entry.related {
        let related-entry = get-glossary-term(related)
        if related-entry != none and "related" not in related-entry {
          // Add reverse relationship if it doesn't exist
          related-entry.insert("related", (entry.term,))
        }
      }
    }
  }
}

// Get glossary statistics
#let get-glossary-stats() = {
  let total = glossary-entries.len()
  let categories = get-glossary-categories()
  let avg-term-len = (
    glossary-entries.map(e => e.term.len()).sum(default: 0) / total
  )
  let avg-def-len = (
    glossary-entries.map(e => e.definition.len()).sum(default: 0) / total
  )

  (
    total: total,
    categories: categories.len(),
    avg-term-length: calc.round(avg-term-len, digits: 1),
    avg-definition-length: calc.round(avg-def-len, digits: 1),
  )
}

// Export glossary to different formats
#let export-glossary(format: "typst") = {
  if format == "typst" {
    [#glossary-entries]
  } else if format == "json" {
    [#repr(glossary-entries)]
  } else if format == "csv" {
    let csv-lines = ("Term,Category,Definition,Related",)
    for e in glossary-entries {
      let related-str = if "related" in e { e.related.join("; ") } else { "" }
      let line = (
        "\""
          + e.term.replace("\"", "\"\"")
          + "\",\""
          + e.at("category", default: "").replace("\"", "\"\"")
          + "\",\""
          + e.definition.replace("\"", "\"\"")
          + "\",\""
          + related-str.replace("\"", "\"\"")
          + "\""
      )
      csv-lines.push(line)
    }
    csv-lines.join("\n")
  } else {
    panic("Unsupported export format: " + format)
  }
}

// Import glossary entries
#let import-glossary(new-entries) = {
  // Validate format
  for entry in new-entries {
    if (
      type(entry) != dictionary
        or "term" not in entry
        or "definition" not in entry
    ) {
      panic(
        "Invalid glossary format. Expected: (term: \"...\", definition: \"...\", category: \"...\", related: (...))",
      )
    }
  }

  // Merge with existing
  let merged = glossary-entries + new-entries

  // Remove duplicates (keep last occurrence)
  let seen = (:)
  let deduped = ()
  for entry in merged.rev() {
    if entry.term not in seen {
      seen.insert(entry.term, true)
      deduped.push(entry)
    }
  }

  deduped.rev()
}

// Create glossary index for quick lookup
#let create-glossary-index() = {
  let index = (:)
  for entry in glossary-entries {
    index.insert(entry.term, entry)
  }
  index
}

// Quick lookup with caching
#let _glossary-cache = state("glossary-cache", none)

#let get-glossary-fast(term) = {
  locate(loc => {
    let cache = _glossary-cache.at(loc)
    if cache == none {
      cache = create-glossary-index()
      _glossary-cache.update(cache)
    }
    cache.at(term, default: none)
  })
}

// Enhanced abbreviation-glossary integration utilities

// Check if a term exists in either abbreviations or glossary
#let term-exists(term, check-abbrevs: true, check-glossary: true) = {
  let found = false
  if check-abbrevs {
    import "abbreviations.typ": abbreviations
    found = (
      found
        or (abbreviations.find(e => e.key == term or e.short == term) != none)
    )
  }
  if check-glossary {
    found = found or (glossary-entries.find(e => e.term == term) != none)
  }
  found
}

// Get comprehensive term information (from either system)
#let get-term-info(term) = {
  import "abbreviations.typ": abbreviations

  // Check abbreviations first
  let abbrev = abbreviations.find(e => e.key == term or e.short == term)
  if abbrev != none {
    return (
      type: "abbreviation",
      key: abbrev.key,
      short: abbrev.short,
      long: abbrev.long,
      definition: abbrev.long,
    )
  }

  // Check glossary
  let glossary = glossary-entries.find(e => e.term == term)
  if glossary != none {
    return (
      type: "glossary",
      term: glossary.term,
      definition: glossary.definition,
      category: glossary.at("category", default: "General"),
      related: glossary.at("related", default: ()),
    )
  }

  none
}

// Unified term reference (works with both abbreviations and glossary)
#let term(term, link: true, expand: true) = {
  let info = get-term-info(term)
  if info == none {
    text(fill: red, weight: "bold")[#term (?) ]
  } else if info.type == "abbreviation" {
    import "abbreviations.typ": abbrev
    abbrev(info.short, expand: expand)
  } else {
    glossary(info.term, link: link, expand: expand)
  }
}

// Create combined abbreviations and glossary index
#let create-combined-index() = {
  import "abbreviations.typ": abbreviations

  let index = (:)

  // Add abbreviations
  for entry in abbreviations {
    index.insert(entry.short, (type: "abbreviation", data: entry))
    index.insert(entry.key, (type: "abbreviation", data: entry))
  }

  // Add glossary terms
  for entry in glossary-entries {
    index.insert(entry.term, (type: "glossary", data: entry))
  }

  index
}

// Combined search across abbreviations and glossary
#let search-terms(pattern, sources: ("abbreviations", "glossary")) = {
  import "abbreviations.typ": abbreviations

  let results = ()

  if "abbreviations" in sources {
    let abbrev-results = abbreviations
      .filter(entry => {
        (
          entry.key.contains(pattern)
            or entry.short.contains(pattern)
            or entry.long.contains(pattern)
        )
      })
      .map(entry => (type: "abbreviation", data: entry))
    results += abbrev-results
  }

  if "glossary" in sources {
    let glossary-results = glossary-entries
      .filter(entry => {
        (
          entry.term.contains(pattern)
            or entry.definition.contains(pattern)
            or entry.at("category", default: "").contains(pattern)
        )
      })
      .map(entry => (type: "glossary", data: entry))
    results += glossary-results
  }

  results
}

// Get combined statistics
#let get-combined-stats() = {
  import "abbreviations.typ": abbreviations, get-abbreviation-stats

  let abbrev-stats = get-abbreviation-stats()
  let glossary-stats = get-glossary-stats()

  (
    abbreviations: abbrev-stats,
    glossary: glossary-stats,
    total-terms: abbrev-stats.total + glossary-stats.total,
    total-categories: glossary-stats.categories,
  )
}

// Generate automated glossary page with page references
#let generate-glossary-entry(entry, include-page-refs: true) = {
  [#block({
      text(weight: "bold", size: 11pt, entry.term)
      [: #entry.definition]
      let pages = entry.at("page-references", default: ())
      if include-page-refs and pages.len() > 0 {
        text(style: "italic", size: 9pt)[ (pp. #pages.map(str).join(", "))]
      }
      let related = entry.at("related", default: ())
      if related.len() > 0 {
        linebreak()
        text(fill: colors.secondary, size: 9pt)[See also: #related.join(", ")]
      }
    })#label("glossary-" + entry.term)]
}

#let generate-glossary-page(
  title: "Glossary",
  include-auto-extracted: true,
  include-page-refs: true,
  include-categories: true,
  sort-by: "term",
  include-abbreviations: true,
  include-manual-glossary: true,
  include-extracted-terms: true,
  show-statistics: false,
  show-validation: false,
) = context {
  let terms = (:)
  let pages = _term-page-references.final()
  if include-extracted-terms and include-auto-extracted {
    terms = get-extracted-glossary()
  }
  if include-manual-glossary {
    for entry in glossary-entries {
      entry.insert("page-references", pages.at(entry.term, default: ()))
      terms.insert(entry.term, entry)
    }
  }
  if include-abbreviations {
    import "abbreviations.typ": abbreviations
    for entry in abbreviations {
      if entry.key not in terms {
        terms.insert(entry.key, (
          term: entry.key,
          definition: entry.long,
          category: "Abbreviations",
          related: (),
        ))
      }
    }
  }
  assert(
    sort-by in ("term", "category"),
    message: "Glossary sort-by must be term or category.",
  )
  let entries = terms.values().sorted(key: e => e.term)
  set page(margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm))
  heading(title, numbering: none)
  v(1cm)
  if show-validation {
    let validation = validate-glossary()
    assert(
      validation.errors.len() == 0,
      message: "Glossary validation failed: " + validation.errors.join("; "),
    )
  }
  if entries.len() == 0 { [No glossary terms defined.] }
  if include-categories or sort-by == "category" {
    let categories = entries
      .map(e => e.at("category", default: "General"))
      .dedup()
      .sorted()
    for category in categories {
      if include-categories { heading(category, level: 2, numbering: none) }
      for entry in entries.filter(e => (
        e.at("category", default: "General") == category
      )) {
        generate-glossary-entry(entry, include-page-refs: include-page-refs)
        v(0.3em)
      }
    }
  } else {
    for entry in entries {
      generate-glossary-entry(entry, include-page-refs: include-page-refs)
      v(0.3em)
    }
  }
  if show-statistics {
    text(size: 10pt)[Glossary Statistics: #entries.len() terms.]
  }
}

#let extract-terms-from-content(content, context-patterns: ()) = {
  panic(
    "Automatic glossary extraction is unsupported. Use explicit glossary-term(term, definition) markers; extract-technical-terms(string) provides suggestions only.",
  )
}

#let add-glossary-terms(new-terms) = {
  for (term, data) in new-terms {
    if type(data) == dictionary and "definition" in data {
      let entry = (
        term: term,
        definition: data.definition,
        category: data.at("category", default: "General"),
        related: data.at("related", default: ()),
        auto-extracted: data.at("auto-extracted", default: false),
      )
      glossary-entries.push(entry)
    }
  }
}

// Create glossary index page
#let generate-glossary-index() = context {
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
  )

  align(center)[
    #text(size: 16pt, weight: "bold", fill: colors.primary)[Glossary Index]
  ]

  v(1cm)

  let all-terms = generate-full-glossary()

  // Create two-column index
  let columns = 2
  let terms-per-column = calc.ceil(all-terms.len() / columns)

  table(
    columns: (1fr, 1fr),
    stroke: none,
    align: left,

    // Column 1
    ..for i in range(0, calc.min(terms-per-column, all-terms.len())) {
      let entry = all-terms.at(i)
      ([#native-glossary-link(label("glossary-" + entry.term))[#entry.term]],)
    },

    // Column 2
    ..for i in range(terms-per-column, all-terms.len()) {
      let entry = all-terms.at(i)
      ([#native-glossary-link(label("glossary-" + entry.term))[#entry.term]],)
    }
  )
}
